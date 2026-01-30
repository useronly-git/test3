from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query()
async def status_change(call: CallbackQuery):
    status, user_id = call.data.split(":")

    text = "☕ Ваш заказ готовится" if status == "cook" else "✅ Ваш заказ готов!"
    await call.bot.send_message(user_id, text)
    await call.answer("Статус отправлен")
