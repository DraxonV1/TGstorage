import uvicorn
import os
import asyncio
import logging
from .api import api
from .database import init_db, get_expired_files, delete_file_db
from .bot import cluster
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def cleanup_task():
    while True:
        try:
            expired_files = await get_expired_files()
            for file in expired_files:
                try: 
                    await cluster.delete_messages(settings.CHANNEL_ID, file['message_id'])
                except: 
                    pass
                await delete_file_db(file['file_id'])
        except: pass
        await asyncio.sleep(3600)

@api.on_event("startup")
async def on_startup():
    await init_db()
    # Initialize and verify all bots in the cluster
    asyncio.create_task(cluster.start_all())
    asyncio.create_task(cleanup_task())

def main():
    """CLI entry point for the storage server"""
    # Using 8082 to ensure fresh socket
    uvicorn.run("tgstorage.api:api", host="0.0.0.0", port=8082, reload=False, workers=1)

if __name__ == "__main__":
    main()
