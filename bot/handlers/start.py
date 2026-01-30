from aiogram import Router
from aiogram.types import Message, WebAppInfo
from aiogram.filters import Command
from config import WEBAPP_URL

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "☕ Добро пожаловать!\nОформляйте заказ онлайн 👇",
        reply_markup={
            "keyboard": [[{
                "text": "📱 Меню",
                "web_app": WebAppInfo(url=WEBAPP_URL)
            }]],
            "resize_keyboard": True
        }
    )
