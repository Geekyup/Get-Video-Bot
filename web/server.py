import os
import uuid
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.bot import start_bot, bot
from app.utils.logger import logger
from app.services.video_downloader import download_for_web
from app.services.cleanup import delete_file_later
from app.config import settings
from web.schemas import VideoRequest


# ==================== ПУТИ ====================

# web/
WEB_DIR = Path(__file__).resolve().parent
# корень проекта (там, где main.py)
BASE_DIR = WEB_DIR.parent

TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

MAX_WEB_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = asyncio.create_task(start_bot())
    logger.info("FastAPI server started!")
    try:
        yield
    finally:
        bot_task.cancel()
        await bot.session.close()


# ==================== ПРИЛОЖЕНИЕ ====================

app = FastAPI(lifespan=lifespan)

# гарантируем наличие папок (на проде, где их может не быть)
os.makedirs(STATIC_DIR / "js", exist_ok=True)
os.makedirs(STATIC_DIR / "css", exist_ok=True)

# static по реальному пути: web/static
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ==================== ROUTES ====================

@app.get("/")
async def root():
    # web/templates/index.html
    return FileResponse(TEMPLATES_DIR / "index.html")


@app.post("/api/download")
async def download_video_api(video: VideoRequest):
    """API для Mini App - до 2 GB"""
    try:
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.mp4"

        title, size = await download_for_web(video.url, filename, MAX_WEB_SIZE)

        if not os.path.exists(filename):
            return JSONResponse(
                status_code=400,
                content={"error": "Не удалось скачать видео"},
            )

        if size > MAX_WEB_SIZE:
            os.remove(filename)
            return JSONResponse(
                status_code=400,
                content={"error": "Видео слишком большое (>2 GB)"},
            )

        # Удаление через 15 минут
        asyncio.create_task(delete_file_later(filename, 900))

        return JSONResponse(
            {
                "success": True,
                "file_id": file_id,
                "title": title,
                "size": size,
            }
        )

    except Exception as e:
        logger.exception("Error in /api/download")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )


@app.get("/api/file/{file_id}")
async def get_file(file_id: str):
    filename = f"{file_id}.mp4"

    if not os.path.exists(filename):
        return JSONResponse(
            status_code=404,
            content={"error": "Файл не найден"},
        )

    return FileResponse(
        filename,
        media_type="video/mp4",
        filename="video.mp4",
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "bot": "running", "api": "running"}
