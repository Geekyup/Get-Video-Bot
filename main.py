import asyncio
import os
import uuid
from contextlib import asynccontextmanager
import yt_dlp
import json
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# ==================== КОНФИГУРАЦИЯ ====================
load_dotenv() 

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# ==================== AIOGRAM SETUP ====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# НАСТРОЙКИ С ОПЦИОНАЛЬНЫМ ЛИМИТОМ
def get_ydl_opts(filename, max_size=None):
    opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
    }
    
    if max_size:
        opts['max_filesize'] = max_size
    
    return opts

@dp.message(CommandStart())
async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎬 Открыть Video Downloader",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "👋 Привет! Выбери способ скачивания:\n\n"
        "📱 <b>Mini App</b> (рекомендуется)\n"
        "└ До 2 GB\n"
        "└ Прямая загрузка на устройство\n"
        "└ Быстрее и удобнее\n\n"
        "💬 <b>Отправить ссылку в чат</b>\n"
        "└ До 50 МБ\n"
        "└ Видео сохранится в Telegram\n\n"
        "Нажми кнопку ниже для Mini App ⬇️",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@dp.message(F.text.regexp(r'https?://'))
async def download_video(message: Message):
    url = message.text.strip()
    
    status_msg = await message.answer("⏳ Скачиваю видео...")
    
    filename = f"video_{message.from_user.id}_{message.message_id}.mp4"
    
    try:
        # Для бота лимит 50 МБ
        ydl_opts = get_ydl_opts(filename, max_size=50 * 1024 * 1024)
        
        await asyncio.to_thread(
            lambda: yt_dlp.YoutubeDL(ydl_opts).download([url])
        )
        
        if not os.path.exists(filename):
            await status_msg.edit_text("❌ Не удалось скачать видео. Проверь ссылку.")
            return
        
        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await status_msg.edit_text(
                "❌ Видео слишком большое (больше 50 МБ).\n\n"
                "💡 Используй Mini App для больших файлов:\n"
                "Нажми на кнопку в /start"
            )
            os.remove(filename)
            return
        
        await status_msg.edit_text("📤 Отправляю видео...")
        
        video_file = FSInputFile(filename)
        await message.answer_video(
            video=video_file,
            caption="✅ Готово!"
        )
        
        await status_msg.delete()
        
    except yt_dlp.utils.DownloadError:
        await status_msg.edit_text(
            "❌ Ошибка скачивания. Возможные причины:\n"
            "• Неверная ссылка\n"
            "• Видео недоступно\n"
            "• Платформа не поддерживается"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

@dp.message()
async def handle_other(message: Message):
    await message.answer("❌ Пожалуйста, отправь ссылку на видео или используй Mini App.")

async def start_bot():
    """Запуск бота"""
    print("🤖 Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

# ==================== FASTAPI ====================
class VideoRequest(BaseModel):
    url: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = asyncio.create_task(start_bot())
    print("🌐 FastAPI сервер запущен!")
    
    try:
        yield
    finally:
        bot_task.cancel()
        await bot.session.close()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ ТОЛЬКО ЭТО ДОБАВЛЕНО - создание твоих папок
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/css", exist_ok=True)

async def delete_file_later(filename: str, delay: int):
    """Удаляет файл через заданное время"""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"🗑️ Удален файл: {filename}")
    except Exception as e:
        print(f"❌ Ошибка удаления {filename}: {e}")

@app.get("/")
async def root():
    return FileResponse("templates/index.html")

@app.post("/api/download")
async def download_video_api(video: VideoRequest):
    """API для Mini App - до 2 GB"""
    try:
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp4"
        
        # Для Mini App лимит 2 GB
        ydl_opts = get_ydl_opts(filename, max_size=2 * 1024 * 1024 * 1024)
        
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video.url, download=True)
                return info.get('title', 'video')
        
        title = await asyncio.to_thread(download)
        
        if not os.path.exists(filename):
            return JSONResponse(
                status_code=400,
                content={"error": "Не удалось скачать видео"}
            )
        
        file_size = os.path.getsize(filename)
        
        if file_size > 2 * 1024 * 1024 * 1024:
            os.remove(filename)
            return JSONResponse(
                status_code=400,
                content={"error": "Видео слишком большое (>2 GB)"}
            )
        
        # Удаление через 15 минут
        asyncio.create_task(delete_file_later(filename, 900))
        
        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "title": title,
            "size": file_size
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/api/file/{file_id}")
async def get_file(file_id: str):
    filename = f"{file_id}.mp4"
    
    if not os.path.exists(filename):
        return JSONResponse(
            status_code=404,
            content={"error": "Файл не найден"}
        )
    
    return FileResponse(
        filename,
        media_type="video/mp4",
        filename="video.mp4"
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "bot": "running", "api": "running"}

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
