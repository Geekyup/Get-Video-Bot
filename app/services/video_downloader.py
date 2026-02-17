import os
import asyncio
from typing import Optional, Callable, Any
import yt_dlp

def get_ydl_opts(filename: str, max_size: Optional[int] = None) -> dict:
    opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": filename,
        "quiet": True,
        "no_warnings": True,
    }
    if max_size:
        opts["max_filesize"] = max_size
    return opts

async def run_in_thread(func: Callable[[], Any]) -> Any:
    return await asyncio.to_thread(func)

async def download_for_bot(url: str, filename: str, max_size_bytes: int) -> bool:
    opts = get_ydl_opts(filename, max_size=max_size_bytes)

    def _download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    await run_in_thread(_download)
    return os.path.exists(filename)

async def download_for_web(url: str, filename: str, max_size_bytes: int) -> tuple[str, int]:
    opts = get_ydl_opts(filename, max_size=max_size_bytes)

    def _download() -> tuple[str, int]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
        size = os.path.getsize(filename) if os.path.exists(filename) else 0
        return title, size

    title, size = await run_in_thread(_download)
    return title, size
