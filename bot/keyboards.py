from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def order_status_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="☕ Готовится", callback_data=f"cook:{user_id}"),
            InlineKeyboardButton(text="✅ Готов", callback_data=f"ready:{user_id}")
        ]
    ])
