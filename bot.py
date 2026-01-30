import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import BOT_TOKEN, ADMIN_CHAT_ID
from db import (
    init_db, get_or_create_user, get_user_profile,
    get_user_orders, update_order_status, get_order
)
from keyboards import main_menu_kb, order_status_admin_kb

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = get_or_create_user(message.from_user.id, message.from_user.full_name)
    await message.answer(
        "Привет! Это кофейня ☕\n\n"
        "• Заказывай напитки навынос или на месте\n"
        "• Оформляй заказ ко времени\n"
        "• Управляй профилем и смотри историю заказов\n\n"
        "Нажми «Меню / Заказ», чтобы открыть мини-приложение.",
        reply_markup=main_menu_kb()
    )

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    profile = get_user_profile(message.from_user.id)
    if not profile:
        await message.answer("Профиль не найден. Напиши /start ещё раз.")
        return
    text = (
        f"👤 Профиль\n\n"
        f"Имя: {profile.get('name') or 'не указано'}\n"
        f"Телефон: {profile.get('phone') or 'не указан'}\n\n"
        f"Изменить данные можно в мини-приложении."
    )
    await message.answer(text, reply_markup=main_menu_kb())

@dp.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message):
    profile = get_user_profile(message.from_user.id)
    if not profile:
        await message.answer("Профиль не найден. Напиши /start ещё раз.")
        return
    orders = get_user_orders(profile["id"])
    if not orders:
        await message.answer("У тебя пока нет заказов.", reply_markup=main_menu_kb())
        return

    lines = ["📦 Твои заказы:"]
    for o in orders[:10]:
        lines.append(
            f"#{o['id']} — {o['status']} — {o['total_price']/100:.2f} ₽"
            + (f" — ко времени {o['pickup_time']}" if o['pickup_time'] else "")
        )
    await message.answer("\n".join(lines), reply_markup=main_menu_kb())

# === Приём заказов из mini app через /webhook-like endpoint ===
# Предполагаем, что mini app отправляет данные через HTTP на backend,
# а backend уже дергает этот бот через sendMessage или отдельный токен.
# Ниже — хендлер для callback-кнопок статуса заказа.

@dp.callback_query(F.data.startswith("order_status:"))
async def order_status_callback(call: CallbackQuery):
    _, order_id_str, status = call.data.split(":")
    order_id = int(order_id_str)
    update_order_status(order_id, status)
    order = get_order(order_id)
    if order:
        # уведомление клиента
        # здесь нужно хранить tg_id пользователя в orders или доставать через join
        # для простоты считаем, что в orders есть поле user_tg_id (можно добавить в БД)
        pass  # место для доработки: отправка статуса клиенту

    await call.answer("Статус обновлён")
    await call.message.edit_reply_markup(
        reply_markup=order_status_admin_kb(order_id)
    )

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
