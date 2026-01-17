from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Response, Depends, Header, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import secrets
import datetime
import shutil
import re
import asyncio
import logging
from typing import List, Optional
from config import settings
from database import (
    add_file, get_file_by_id, delete_file_db, 
    get_file_by_share_token, increment_view_count,
    list_files, get_stats, verify_key_db, init_db
)
from bot import cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI(title="TG Storage Cluster API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Flexible Authentication
async def verify_api_key(
    x_api_key: Optional[str] = Header(None), 
    key: Optional[str] = Query(None)
):
    provided_key = (x_api_key or key or "").strip()
    if not provided_key:
        logger.error("No API key provided")
        raise HTTPException(status_code=403, detail="API Key required")
        
    if await verify_key_db(provided_key):
        return provided_key
        
    if provided_key == settings.ADMIN_API_KEY.strip():
        return provided_key

    logger.error(f"Auth failed. Provided: {provided_key}")
    raise HTTPException(status_code=403, detail="Invalid API Key")

@api.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    })

@api.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

async def start_bot():
    await init_db()
    await cluster.start_all()

@api.on_event("startup")
async def startup():
    asyncio.create_task(start_bot())

@api.post("/upload")
async def upload(
    file: UploadFile = File(...), 
    expiration_days: int = Form(None),
    password: str = Form(None),
    auth: str = Depends(verify_api_key)
):
    bot = await cluster.get_healthy_bot()
    if not bot:
        raise HTTPException(status_code=503, detail="No healthy bots available")

    temp_path = f"temp_{secrets.token_hex(4)}_{file.filename}"
    try:
        def save_file():
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return os.path.getsize(temp_path)

        file_size = await asyncio.to_thread(save_file)
        logger.info(f"Uploading {file.filename} via {bot._custom_name}")
        
        is_video = file.content_type and "video" in file.content_type.lower()
        
        with open(temp_path, 'rb') as doc_file:
            if is_video:
                message = await asyncio.wait_for(
                    bot.send_video(chat_id=settings.CHANNEL_ID, video=doc_file, filename=file.filename, supports_streaming=True),
                    timeout=600
                )
            else:
                message = await asyncio.wait_for(
                    bot.send_document(chat_id=settings.CHANNEL_ID, document=doc_file, filename=file.filename),
                    timeout=300
                )
        
        media = message.video or message.document
        file_id = media.file_id
        share_token = secrets.token_urlsafe(16)
        exp_date = (datetime.datetime.now() + datetime.timedelta(days=expiration_days)).isoformat() if expiration_days else None
        
        await add_file(file_id, message.message_id, file.filename, file_size, file.content_type or "application/octet-stream", exp_date, share_token, password)
        
        return {
            "status": "success", 
            "file_id": file_id, 
            "direct_link": f"{settings.BASE_URL}/dl/{file_id}/{file.filename}", 
            "share_link": f"{settings.BASE_URL}/share/{share_token}"
        }
    except Exception as e:
        logger.error(f"Upload failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        def cleanup():
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
        await asyncio.to_thread(cleanup)

async def stream_file_response(file_data, filename, bot, request: Request):
    await increment_view_count(file_data['file_id'])
    file_size = file_data['file_size']
    mime = file_data['mime_type']
    
    range_header = request.headers.get("Range")
    start_byte = 0
    end_byte = file_size - 1
    status_code = 200
    
    if range_header:
        match = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        if match:
            start_byte = int(match.group(1))
            if match.group(2):
                end_byte = int(match.group(2))
            status_code = 206

    content_length = end_byte - start_byte + 1

    async def stream_file(url, start, end):
        import httpx
        proxy_url = None
        proxy_host = getattr(settings, "PROXY_HOST", None)
        proxy_port = getattr(settings, "PROXY_PORT", None)
        proxy_user = getattr(settings, "PROXY_USER", None)
        proxy_pass = getattr(settings, "PROXY_PASS", None)
        if proxy_host and proxy_port:
            if proxy_user and proxy_pass:
                proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
            else:
                proxy_url = f"http://{proxy_host}:{proxy_port}"

        headers = {"Range": f"bytes={start}-{end}"}
        async with httpx.AsyncClient(proxy=proxy_url) as client:
            async with client.stream("GET", url, headers=headers) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk

    try:
        tg_file = await bot.get_file(file_data['file_id'])
        disposition = "inline" if any(x in mime for x in ["image", "text", "pdf", "video", "audio"]) else "attachment"
        headers = {
            "Accept-Ranges": "bytes", 
            "Content-Length": str(content_length), 
            "Content-Type": mime, 
            "Content-Disposition": f"{disposition}; filename=\"{filename}\""
        }
        if status_code == 206:
            headers["Content-Range"] = f"bytes {start_byte}-{end_byte}/{file_size}"

        return StreamingResponse(stream_file(tg_file.file_path, start_byte, end_byte), status_code=status_code, headers=headers)
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise HTTPException(status_code=500, detail="Error streaming from Telegram")

@api.get("/share/{token}")
async def get_share_page(token: str, request: Request):
    file_data = await get_file_by_share_token(token)
    if not file_data:
        raise HTTPException(status_code=404, detail="Link expired or invalid")
    bot = await cluster.get_healthy_bot()
    if not bot: raise HTTPException(status_code=503, detail="Bots unavailable")
    return await stream_file_response(file_data, file_data['file_name'], bot, request)

@api.get("/debug/db")
async def debug_db(auth: str = Depends(verify_api_key)):
    files = await list_files(100, 0)
    return {"count": len(files), "files": [dict(f) for f in files]}

@api.get("/stats")
async def get_system_stats(auth: str = Depends(verify_api_key)):
    return await get_stats()

@api.get("/files")
async def list_all_files(limit: int = 50, offset: int = 0, search: str = None, auth: str = Depends(verify_api_key)):
    logger.info(f"Listing files: limit={limit}, offset={offset}, search={search}")
    files = await list_files(limit, offset, search)
    result = [dict(f) for f in files]
    logger.info(f"Found {len(result)} files")
    return result

@api.get("/f/{file_id}/{filename}")
@api.get("/dl/{file_id}/{filename}")
async def download_file(file_id: str, filename: str, request: Request, password: str = None):
    file_data = await get_file_by_id(file_id)
    if not file_data: raise HTTPException(status_code=404, detail="File not found")
    if file_data['password'] and file_data['password'] != password: raise HTTPException(status_code=403, detail="Password required")
    bot = await cluster.get_healthy_bot()
    if not bot: raise HTTPException(status_code=503, detail="Bots unavailable")
    return await stream_file_response(file_data, filename, bot, request)

@api.delete("/file/{file_id}")
async def delete_file_endpoint(file_id: str, auth: str = Depends(verify_api_key)):
    file_data = await get_file_by_id(file_id)
    if not file_data: raise HTTPException(status_code=404, detail="File not found")
    try: await cluster.delete_messages(settings.CHANNEL_ID, file_data['message_id'])
    except Exception as e: logger.error(f"Error deleting Telegram message: {e}")
    await delete_file_db(file_id)
    return {"status": "success", "message": "File deleted"}