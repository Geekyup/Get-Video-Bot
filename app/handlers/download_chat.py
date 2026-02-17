import os
from aiogram.types import Message, FSInputFile
import yt_dlp

from app.services.video_downloader import download_for_bot

MAX_BOT_SIZE = 50 * 1024 * 1024  # 50 MB

async def download_video(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("⏳ Скачиваю видео...")

    filename = f"video_{message.from_user.id}_{message.message_id}.mp4"

    try:
        await download_for_bot(url, filename, max_size_bytes=MAX_BOT_SIZE)

        if not os.path.exists(filename):
            await status_msg.edit_text("❌ Не удалось скачать видео. Проверь ссылку.")
            return

        file_size = os.path.getsize(filename)
        if file_size > MAX_BOT_SIZE:
            await status_msg.edit_text(
                "❌ Видео слишком большое (больше 50 МБ).\n\n"
                "💡 Используй Mini App для больших файлов:\n"
                "Нажми на кнопку в /start"
            )
            os.remove(filename)
            return

        await status_msg.edit_text("📤 Отправляю видео...")

        video_file = FSInputFile(filename)
        await message.answer_video(video=video_file, caption="✅ Готово!")

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
