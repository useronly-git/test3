from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from config import WEBAPP_URL

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="☕ Меню / Заказ", web_app=WebAppInfo(url=f"{WEBAPP_URL}/")),
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="📦 Мои заказы"),
            ],
        ],
        resize_keyboard=True
    )

def order_status_admin_kb(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Принят",
                    callback_data=f"order_status:{order_id}:accepted"
                ),
                InlineKeyboardButton(
                    text="Готовится",
                    callback_data=f"order_status:{order_id}:preparing"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Готов",
                    callback_data=f"order_status:{order_id}:ready"
                ),
                InlineKeyboardButton(
                    text="Выдан",
                    callback_data=f"order_status:{order_id}:done"
                ),
            ],
        ]
    )
