from aiogram.types import Message

async def handle_other(message: Message):
    await message.answer("❌ Пожалуйста, отправь ссылку на видео или используй Mini App.")
