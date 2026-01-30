from aiogram import Router
from aiogram.types import Message
from database import DB
import json
import aiosqlite
from config import STAFF_CHAT_ID
from keyboards import order_status_kb

router = Router()

@router.message()
async def webapp_handler(message: Message):
    if not message.web_app_data:
        return

    data = json.loads(message.web_app_data.data)
    items = ", ".join(data["items"])
    total = data["total"]
    time = data["time"]

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO orders (user_id, items, total, status, time) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, items, total, "new", time)
        )
        await db.commit()

    await message.answer("✅ Заказ принят!")

    await message.bot.send_message(
        STAFF_CHAT_ID,
        f"☕ Новый заказ\n\n"
        f"От: {message.from_user.full_name}\n"
        f"Позиции: {items}\n"
        f"Сумма: {total} ₽\n"
        f"Ко времени: {time}",
        reply_markup=order_status_kb(message.from_user.id)
    )
