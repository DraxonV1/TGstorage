from telegram import Bot
from telegram.request import HTTPXRequest
from .config import settings
import os
import hashlib
import logging
import asyncio

logger = logging.getLogger(__name__)

class BotCluster:
    def __init__(self):
        self.bots = []
        self.current_idx = 0
        self._initialize_bots()

    def _initialize_bots(self):
        self.bots = []
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
        
        request = HTTPXRequest(proxy_url=proxy_url) if proxy_url else None

        for token in settings.bot_token_list:
            token_hash = hashlib.md5(token.encode()).hexdigest()[:8]
            bot = Bot(token=token, request=request)
            bot._custom_name = f"bot_{token_hash}"
            self.bots.append(bot)

    async def start_all(self):
        if not self.bots:
            self._initialize_bots()
        for bot in self.bots:
            try:
                me = await asyncio.wait_for(bot.get_me(), timeout=10)
                logger.info(f"Bot {bot._custom_name} (@{me.username}) is ready.")
            except Exception as e:
                logger.error(f"Error verifying {bot._custom_name}: {e}")

    async def stop_all(self):
        pass

    def get_bot(self):
        if not self.bots:
            self._initialize_bots()
        if not self.bots:
            return None
        bot = self.bots[self.current_idx % len(self.bots)]
        self.current_idx = (self.current_idx + 1) % len(self.bots)
        return bot

    async def delete_messages(self, chat_id, message_ids):
        bot = self.get_bot()
        if not bot:
            logger.error("No bots available for deletion")
            return
        if not isinstance(message_ids, list):
            message_ids = [message_ids]
        for msg_id in message_ids:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Error deleting message {msg_id}: {e}")

    async def get_healthy_bot(self):
        if not self.bots:
            self._initialize_bots()
            
        for _ in range(len(self.bots)):
            bot = self.get_bot()
            if not bot: continue
            try:
                await asyncio.wait_for(bot.get_me(), timeout=5)
                return bot
            except:
                logger.warning(f"Bot {bot._custom_name} failed health check, trying another...")
                continue
        return None

    async def send_video(self, chat_id, video, filename, supports_streaming=True):
        bot = await self.get_healthy_bot()
        if not bot: raise Exception("No healthy bots available")
        return await bot.send_video(
            chat_id=chat_id, 
            video=video, 
            caption=filename, 
            supports_streaming=supports_streaming
        )

    async def send_document(self, chat_id, document, filename):
        bot = await self.get_healthy_bot()
        if not bot: raise Exception("No healthy bots available")
        return await bot.send_document(
            chat_id=chat_id, 
            document=document, 
            filename=filename
        )

cluster = BotCluster()