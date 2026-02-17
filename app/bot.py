import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings
from app.utils.logger import logger
from app.services.video_downloader import download_for_bot
from app.handlers import start as start_handlers
from app.handlers import download_chat as download_handlers
from app.handlers import other as other_handlers

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

def register_handlers() -> None:
    # /start
    dp.message.register(start_handlers.cmd_start, CommandStart())
    # ссылки
    dp.message.register(download_handlers.download_video, F.text.regexp(r"https?://"))
    # всё остальное
    dp.message.register(other_handlers.handle_other)

async def start_bot() -> None:
    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    register_handlers()
    await dp.start_polling(bot)
