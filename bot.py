import json
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import BOT_TOKEN, STAFF_CHAT_ID

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

DB = "database.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total INTEGER,
            status TEXT,
            time TEXT
        )""")
        await db.commit()

@dp.message(Command("start"))
async def start(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="☕ Сделать заказ",
            web_app=WebAppInfo(url="https://YOUR_DOMAIN/miniapp/index.html")
        )],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")]
    ])
    await msg.answer("Добро пожаловать в кофейню ☕", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "profile")
async def profile(call: types.CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT name, phone FROM users WHERE user_id=?",
            (call.from_user.id,)
        )
        row = await cur.fetchone()

    text = "👤 Профиль\n"
    text += f"Имя: {row[0] if row else 'не указано'}\n"
    text += f"Телефон: {row[1] if row else 'не указано'}"
    await call.message.answer(text)

@dp.callback_query(lambda c: c.data == "orders")
async def orders(call: types.CallbackQuery):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT id, total, status FROM orders WHERE user_id=?",
            (call.from_user.id,)
        )
        rows = await cur.fetchall()

    if not rows:
        await call.message.answer("У вас пока нет заказов ☕")
        return

    text = "📦 История заказов:\n"
    for r in rows:
        text += f"#{r[0]} — {r[1]}₽ — {r[2]}\n"
    await call.message.answer(text)

async def send_order_to_staff(order_id, text):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ В работе", callback_data=f"status_{order_id}_work")],
        [InlineKeyboardButton(text="✅ Готов", callback_data=f"status_{order_id}_ready")],
        [InlineKeyboardButton(text="📦 Выдан", callback_data=f"status_{order_id}_done")]
    ])
    await bot.send_message(STAFF_CHAT_ID, text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("status_"))
async def change_status(call: types.CallbackQuery):
    _, order_id, status = call.data.split("_")
    status_map = {
        "work": "В работе",
        "ready": "Готов",
        "done": "Выдан"
    }

    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE orders SET status=? WHERE id=?",
            (status_map[status], order_id)
        )
        await db.commit()

        cur = await db.execute(
            "SELECT user_id FROM orders WHERE id=?",
            (order_id,)
        )
        user_id = (await cur.fetchone())[0]

    await bot.send_message(user_id, f"📦 Заказ #{order_id}: {status_map[status]}")
    await call.answer("Статус обновлён")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
