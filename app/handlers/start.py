from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import settings

async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎬 Открыть Video Downloader",
        web_app=WebAppInfo(url=settings.WEBAPP_URL),
    )

    await message.answer(
        (
            "👋 Привет! Выбери способ скачивания:\n\n"
            "📱 <b>Mini App</b> (рекомендуется)\n"
            "└ До 2 GB\n"
            "└ Прямая загрузка на устройство\n"
            "└ Быстрее и удобнее\n\n"
            "💬 <b>Отправить ссылку в чат</b>\n"
            "└ До 50 МБ\n"
            "└ Видео сохранится в Telegram\n\n"
            "Нажми кнопку ниже для Mini App ⬇️"
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )
