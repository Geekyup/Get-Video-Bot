import os
import asyncio
from app.utils.logger import logger

async def delete_file_later(filename: str, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        if os.path.exists(filename):
            os.remove(filename)
            logger.info(f"Deleted file: {filename}")
    except Exception as e:
        logger.error(f"Error deleting {filename}: {e}")
