# backend/bot.py
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

from database import Database
from config import BOT_TOKEN, ADMIN_IDS

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
PROFILE_NAME, PROFILE_PHONE = range(2)


class CoffeeShopBot:
    def __init__(self):
        self.db = Database()
        self.menu = self.load_menu()

    def load_menu(self) -> Dict:
        """Загрузка меню из JSON файла"""
        with open('menu.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id

        # Регистрируем пользователя если его нет
        user_data = await self.db.get_user(user.id)
        if not user_data:
            await self.db.create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            await update.message.reply_text(
                "👋 Добро пожаловать в CoffeeTime!\n"
                "Я помогу вам сделать заказ кофе с собой или на месте.\n\n"
                "Пожалуйста, заполните ваш профиль для удобного оформления заказов."
            )
            return await self.start_profile(update, context)
        else:
            keyboard = [
                [
                    KeyboardButton("🛒 Сделать заказ",
                                   web_app=WebAppInfo(url=f"https://yourdomain.com/index.html?user_id={user.id}")),
                    KeyboardButton("👤 Мой профиль")
                ],
                [
                    KeyboardButton("📋 История заказов"),
                    KeyboardButton("🕐 Заказать ко времени")
                ],
                [
                    KeyboardButton("📞 Связаться с нами"),
                    KeyboardButton("ℹ️ О нас")
                ]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"Привет, {user.first_name}! 👋\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )

    async def start_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало заполнения профиля"""
        await update.message.reply_text(
            "Для начала работы, пожалуйста, укажите ваше имя:",
            reply_markup=ReplyKeyboardRemove()
        )
        return PROFILE_NAME

    async def get_profile_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение имени пользователя"""
        context.user_data['profile_name'] = update.message.text

        keyboard = [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text(
            "Отлично! Теперь нам нужен ваш номер телефона для связи:",
            reply_markup=reply_markup
        )
        return PROFILE_PHONE

    async def get_profile_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение номера телефона"""
        phone = update.message.contact.phone_number if update.message.contact else update.message.text

        user_id = update.effective_user.id
        await self.db.update_user_profile(
            user_id=user_id,
            name=context.user_data['profile_name'],
            phone=phone
        )

        keyboard = [
            [
                KeyboardButton("🛒 Сделать заказ",
                               web_app=WebAppInfo(url=f"https://yourdomain.com/index.html?user_id={user_id}"))
            ]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "✅ Профиль успешно сохранен!\n"
            "Теперь вы можете сделать заказ.",
            reply_markup=reply_markup
        )

        context.user_data.clear()
        return ConversationHandler.END

    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать профиль пользователя"""
        user_id = update.effective_user.id
        user_data = await self.db.get_user(user_id)

        if not user_data:
            return await update.message.reply_text("Профиль не найден.")

        keyboard = [
            [InlineKeyboardButton("✏️ Изменить имя", callback_data="edit_name")],
            [InlineKeyboardButton("📱 Изменить телефон", callback_data="edit_phone")],
            [InlineKeyboardButton("📍 Изменить адрес", callback_data="edit_address")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"👤 **Ваш профиль**\n\n"
            f"**Имя:** {user_data.get('name', 'Не указано')}\n"
            f"**Телефон:** {user_data.get('phone', 'Не указан')}\n"
            f"**Адрес:** {user_data.get('address', 'Не указан')}\n"
            f"**Бонусы:** {user_data.get('bonus_points', 0)} баллов\n"
        )

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    async def show_order_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать историю заказов"""
        user_id = update.effective_user.id
        orders = await self.db.get_user_orders(user_id)

        if not orders:
            return await update.message.reply_text("У вас еще нет заказов.")

        text = "📋 **История ваших заказов:**\n\n"

        for order in orders[:10]:  # Последние 10 заказов
            status_emoji = {
                'new': '🆕',
                'preparing': '👨‍🍳',
                'ready': '✅',
                'completed': '🏁',
                'cancelled': '❌'
            }.get(order['status'], '📝')

            text += (
                f"**Заказ #{order['id']}** {status_emoji}\n"
                f"Дата: {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                f"Сумма: {order['total_amount']} руб.\n"
                f"Статус: {order['status']}\n"
                f"{'-' * 20}\n"
            )

        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    async def handle_web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных из Web App"""
        try:
            data = json.loads(update.effective_message.web_app_data.data)
            user_id = update.effective_user.id

            # Создаем заказ
            order_id = await self.create_order(user_id, data)

            # Отправляем подтверждение
            await update.message.reply_text(
                f"✅ Заказ #{order_id} принят!\n"
                f"Сумма: {data['total']} руб.\n"
                f"Ожидайте уведомлений о статусе заказа."
            )

            # Отправляем заказ администраторам
            await self.send_order_to_admins(order_id, data, user_id)

        except Exception as e:
            logger.error(f"Error handling web app data: {e}")
            await update.message.reply_text("❌ Произошла ошибка при оформлении заказа.")

    async def create_order(self, user_id: int, order_data: Dict) -> int:
        """Создание заказа в базе данных"""
        order_id = await self.db.create_order(
            user_id=user_id,
            items=order_data['items'],
            total_amount=order_data['total'],
            delivery_type=order_data.get('delivery_type', 'pickup'),
            scheduled_time=order_data.get('scheduled_time'),
            address=order_data.get('address'),
            notes=order_data.get('notes', '')
        )
        return order_id

    async def send_order_to_admins(self, order_id: int, order_data: Dict, user_id: int):
        """Отправка заказа администраторам"""
        user_data = await self.db.get_user(user_id)

        order_text = (
            f"🆕 **Новый заказ #{order_id}**\n\n"
            f"**Клиент:** {user_data.get('name', 'Не указано')}\n"
            f"**Телефон:** {user_data.get('phone', 'Не указан')}\n"
            f"**Тип заказа:** {'С собой' if order_data.get('delivery_type') == 'takeaway' else 'На месте'}\n"
            f"**Адрес:** {order_data.get('address', 'Не указан')}\n"
            f"**Время:** {order_data.get('scheduled_time', 'Как можно скорее')}\n"
            f"**Примечания:** {order_data.get('notes', 'Нет')}\n\n"
            f"**Состав заказа:**\n"
        )

        for item in order_data['items']:
            order_text += f"- {item['name']} x{item['quantity']}: {item['price'] * item['quantity']} руб.\n"

        order_text += f"\n**Итого:** {order_data['total']} руб."

        keyboard = [
            [
                InlineKeyboardButton("👨‍🍳 В приготовлении", callback_data=f"status_preparing_{order_id}"),
                InlineKeyboardButton("✅ Готов", callback_data=f"status_ready_{order_id}")
            ],
            [
                InlineKeyboardButton("🏁 Выполнен", callback_data=f"status_completed_{order_id}"),
                InlineKeyboardButton("❌ Отменить", callback_data=f"status_cancelled_{order_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправка всем администраторам
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=order_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error sending to admin {admin_id}: {e}")

    async def update_order_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обновление статуса заказа"""
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith('status_'):
            _, status, order_id = data.split('_')

            # Обновляем статус в базе данных
            await self.db.update_order_status(int(order_id), status)

            # Получаем информацию о заказе
            order = await self.db.get_order(int(order_id))
            if order:
                # Отправляем уведомление клиенту
                status_texts = {
                    'preparing': '👨‍🍳 Ваш заказ начали готовить',
                    'ready': '✅ Ваш заказ готов!',
                    'completed': '🏁 Заказ выполнен',
                    'cancelled': '❌ Заказ отменен'
                }

                if status in status_texts:
                    await context.bot.send_message(
                        chat_id=order['user_id'],
                        text=f"{status_texts[status]}\nЗаказ #{order_id}"
                    )

                # Обновляем сообщение у администратора
                await query.edit_message_text(
                    text=f"✅ Статус заказа #{order_id} обновлен на: {status}",
                    reply_markup=None
                )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        text = update.message.text

        if text == "👤 Мой профиль":
            await self.show_profile(update, context)
        elif text == "📋 История заказов":
            await self.show_order_history(update, context)
        elif text == "🕐 Заказать ко времени":
            keyboard = [[InlineKeyboardButton("🛒 Открыть меню", web_app=WebAppInfo(
                url=f"https://yourdomain.com/index.html?user_id={update.effective_user.id}&scheduled=true"))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Вы можете выбрать время получения заказа при оформлении в меню:",
                reply_markup=reply_markup
            )
        elif text == "📞 Связаться с нами":
            await update.message.reply_text(
                "📞 **Контакты CoffeeTime:**\n\n"
                "📍 Адрес: ул. Кофейная, 123\n"
                "📱 Телефон: +7 (999) 123-45-67\n"
                "🕒 Часы работы: 8:00 - 22:00\n\n"
                "Мы в соцсетях:\n"
                "Instagram: @coffeetime\n"
                "VK: vk.com/coffeetime"
            )
        elif text == "ℹ️ О нас":
            await update.message.reply_text(
                "☕ **CoffeeTime**\n\n"
                "Мы - современная кофейня с любовью к кофе и заботой о клиентах.\n\n"
                "• Свежеобжаренный кофе каждый день\n"
                "• Уютная атмосфера\n"
                "• Бесплатный Wi-Fi\n"
                "• Программа лояльности\n\n"
                "Ждем вас в гости!"
            )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущего действия"""
        await update.message.reply_text(
            "Действие отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    def run(self):
        """Запуск бота"""
        application = Application.builder().token(BOT_TOKEN).build()

        # ConversationHandler для профиля
        profile_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, self.start_profile)],
            states={
                PROFILE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_profile_name)],
                PROFILE_PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, self.get_profile_phone)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )

        # Обработчики
        application.add_handler(CommandHandler('start', self.start))
        application.add_handler(profile_conv)
        application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.handle_web_app_data))
        application.add_handler(CallbackQueryHandler(self.update_order_status, pattern='^status_'))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Запуск бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == 'back_to_main':
            keyboard = [
                [
                    KeyboardButton("🛒 Сделать заказ", web_app=WebAppInfo(
                        url=f"https://yourdomain.com/index.html?user_id={query.from_user.id}")),
                    KeyboardButton("👤 Мой профиль")
                ],
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await query.message.reply_text("Главное меню:", reply_markup=reply_markup)


if __name__ == '__main__':
    bot = CoffeeShopBot()
    bot.run()