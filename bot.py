import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import config
from web_app_handler import WebAppHandler
from database import DatabaseManager, SessionLocal
import json
from datetime import datetime
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class CoffeeShopBot:
    def __init__(self):
        self.web_app_url = config.WEBHOOK_URL + "/webapp" if config.WEBHOOK_URL else "https://your-domain.com/webapp"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user

        # Сохраняем пользователя в БД
        db = SessionLocal()
        try:
            DatabaseManager.get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        finally:
            db.close()

        # Создаем клавиатуру с кнопкой открытия Web App
        keyboard = [
            [InlineKeyboardButton("📱 Открыть меню", web_app=WebAppInfo(url=self.web_app_url))],
            [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders")],
            [InlineKeyboardButton("🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton("📍 Контакты", callback_data="contacts")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Добро пожаловать в **Coffee House**! ☕\n\n"
            "У нас вы можете заказать:\n"
            "• Свежесваренный кофе\n"
            "• Ароматный чай\n"
            "• Вкусные десерты\n"
            "• Сытные завтраки\n\n"
            "🎯 **Особенности:**\n"
            "✅ Заказ навынос и на месте\n"
            "✅ Заказ ко времени\n"
            "✅ Онлайн отслеживание статуса\n"
            "✅ Быстрая доставка\n\n"
            "Нажмите кнопку ниже, чтобы открыть меню и сделать заказ!"
        )

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных из Web App"""
        await WebAppHandler.handle_webapp_data(update, context)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback кнопок"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("confirm_order_"):
            await self._update_order_status(query, "confirmed")
        elif query.data.startswith("preparing_order_"):
            await self._update_order_status(query, "preparing")
        elif query.data.startswith("ready_order_"):
            await self._update_order_status(query, "ready")
        elif query.data.startswith("complete_order_"):
            await self._update_order_status(query, "completed")
        elif query.data.startswith("cancel_order_"):
            await self._update_order_status(query, "cancelled")
        elif query.data == "profile":
            await self._show_profile(query)
        elif query.data == "my_orders":
            await self._show_orders(query)
        elif query.data == "cart":
            await self._show_cart(query)
        elif query.data == "contacts":
            await self._show_contacts(query)
        elif query.data == "help":
            await self._show_help(query)

    async def _update_order_status(self, query, status):
        """Обновление статуса заказа"""
        order_id = int(query.data.split("_")[-1])

        db = SessionLocal()
        try:
            order = DatabaseManager.update_order_status(db, order_id, status)

            if order:
                # Обновляем сообщение для админа
                status_text = {
                    "confirmed": "✅ Подтвержден",
                    "preparing": "👨‍🍳 Готовится",
                    "ready": "📦 Готов к выдаче",
                    "completed": "✅ Выполнен",
                    "cancelled": "❌ Отменен"
                }.get(status, status)

                await query.edit_message_text(
                    f"{query.message.text}\n\n📊 **Статус обновлен:** {status_text}",
                    parse_mode=ParseMode.MARKDOWN
                )

                # Отправляем уведомление клиенту
                user_status_text = {
                    "confirmed": "✅ Ваш заказ подтвержден и начал готовиться!",
                    "preparing": "👨‍🍳 Ваш заказ готовится!",
                    "ready": "📦 Ваш заказ готов к выдаче! Приходите забирать!",
                    "completed": "✅ Заказ выполнен! Спасибо за покупку!",
                    "cancelled": "❌ Ваш заказ был отменен."
                }.get(status, "")

                if user_status_text:
                    try:
                        await query.bot.send_message(
                            chat_id=order.telegram_id,
                            text=f"🔄 **Обновление статуса заказа**\n"
                                 f"Заказ #{order.order_number}\n\n"
                                 f"{user_status_text}"
                        )
                    except:
                        pass
        finally:
            db.close()

    async def _show_profile(self, query):
        """Показать профиль пользователя"""
        db = SessionLocal()
        try:
            user = DatabaseManager.get_or_create_user(
                db=db,
                telegram_id=query.from_user.id,
                username=query.from_user.username,
                first_name=query.from_user.first_name,
                last_name=query.from_user.last_name
            )

            profile_text = (
                f"👤 **Ваш профиль**\n\n"
                f"🆔 ID: `{user.telegram_id}`\n"
                f"👤 Имя: {user.first_name or 'Не указано'} {user.last_name or ''}\n"
                f"📱 Телефон: {user.phone or 'Не указан'}\n"
                f"📧 Email: {user.email or 'Не указан'}\n"
                f"📍 Адрес: {user.address or 'Не указан'}\n\n"
                f"Для редактирования профиля откройте меню 📱"
            )

            keyboard = [
                [InlineKeyboardButton("📱 Открыть меню", web_app=WebAppInfo(url=self.web_app_url))],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
            ]

            await query.message.reply_text(
                profile_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            db.close()

    async def _show_orders(self, query):
        """Показать историю заказов"""
        db = SessionLocal()
        try:
            orders = DatabaseManager.get_user_orders(db, query.from_user.id, limit=5)

            if not orders:
                await query.message.reply_text(
                    "📭 У вас пока нет заказов.\n\n"
                    "Сделайте первый заказ через меню! 📱",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📱 Открыть меню", web_app=WebAppInfo(url=self.web_app_url))]
                    ])
                )
                return

            orders_text = "📋 **Ваши последние заказы:**\n\n"

            for order in orders:
                status_emoji = {
                    "pending": "⏳",
                    "confirmed": "✅",
                    "preparing": "👨‍🍳",
                    "ready": "📦",
                    "completed": "🎉",
                    "cancelled": "❌"
                }.get(order.status, "📝")

                orders_text += (
                    f"{status_emoji} **Заказ #{order.order_number}**\n"
                    f"💰 Сумма: {order.total_amount} руб.\n"
                    f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📦 Статус: {order.status}\n"
                    f"📍 Тип: {'Навынос' if order.order_type == 'takeaway' else 'На месте'}\n"
                    f"────────────────\n"
                )

            keyboard = [
                [InlineKeyboardButton("📱 Открыть меню", web_app=WebAppInfo(url=self.web_app_url))],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
            ]

            await query.message.reply_text(
                orders_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            db.close()

    async def _show_cart(self, query):
        """Показать корзину"""
        db = SessionLocal()
        try:
            cart = DatabaseManager.get_cart(db, query.from_user.id)

            if not cart.items:
                await query.message.reply_text(
                    "🛒 **Ваша корзина пуста**\n\n"
                    "Добавьте товары через меню! 📱",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📱 Открыть меню", web_app=WebAppInfo(url=self.web_app_url))]
                    ])
                )
                return

            cart_text = "🛒 **Ваша корзина:**\n\n"
            total = 0

            for item in cart.items:
                item_total = item.get('price', 0) * item.get('quantity', 1)
                total += item_total

                cart_text += (
                    f"• {item.get('name', 'Товар')} x{item.get('quantity', 1)}\n"
                    f"  Размер: {item.get('size', 'Стандартный')}\n"
                )

                if item.get('addons'):
                    cart_text += f"  Дополнения: {', '.join(item.get('addons', []))}\n"

                cart_text += f"  Цена: {item_total} руб.\n\n"

            cart_text += f"💰 **Итого: {total} руб.**\n\n"
            cart_text += "Для оформления заказа откройте меню 📱"

            keyboard = [
                [InlineKeyboardButton("📱 Открыть меню", web_app=WebAppInfo(url=self.web_app_url))],
                [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
            ]

            await query.message.reply_text(
                cart_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            db.close()

    async def _show_contacts(self, query):
        """Показать контакты"""
        contacts_text = (
            "📍 **Контакты Coffee House**\n\n"
            "🏠 **Адрес:**\n"
            "ул. Кофейная, д. 15\n"
            "Москва, Россия\n\n"
            "📞 **Телефон:**\n"
            "+7 (999) 123-45-67\n\n"
            "🕒 **Часы работы:**\n"
            "Пн-Пт: 8:00 - 22:00\n"
            "Сб-Вс: 9:00 - 23:00\n\n"
            "🚗 **Доставка:**\n"
            "Бесплатно при заказе от 500 руб.\n"
            "Время доставки: 30-60 минут\n\n"
            "💬 **Поддержка:**\n"
            "@coffeehouse_support"
        )

        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
        ]

        await query.message.reply_text(
            contacts_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def _show_help(self, query):
        """Показать справку"""
        help_text = (
            "ℹ️ **Помощь по использованию бота**\n\n"
            "📱 **Как сделать заказ:**\n"
            "1. Нажмите 'Открыть меню'\n"
            "2. Выберите товары\n"
            "3. Перейдите в корзину\n"
            "4. Оформите заказ\n\n"
            "🕒 **Заказ ко времени:**\n"
            "При оформлении заказа выберите 'Ко времени' и укажите удобное время\n\n"
            "📍 **Типы заказа:**\n"
            "• Навынос - самовывоз из кофейни\n"
            "• На месте - употребление в кофейне\n"
            "• Доставка - курьер привезет заказ\n\n"
            "📊 **Отслеживание заказа:**\n"
            "• Статус заказа обновляется в реальном времени\n"
            "• Вы получаете уведомления\n"
            "• История заказов сохраняется\n\n"
            "👤 **Профиль:**\n"
            "Сохраните свои данные для быстрого оформления\n\n"
            "❓ **Проблемы:**\n"
            "Если возникли проблемы, напишите @coffeehouse_support"
        )

        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
        ]

        await query.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    async def back_to_main(self, query):
        """Вернуться в главное меню"""
        await self.start(query, None)


def main():
    """Запуск бота"""
    # Создание приложения
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Инициализация бота
    bot = CoffeeShopBot()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("menu", bot.start))

    # Обработчик данных из Web App
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bot.handle_webapp_data))

    # Обработчик callback кнопок
    application.add_handler(CallbackQueryHandler(bot.button_callback))

    # Запуск бота
    if config.WEBHOOK_URL:
        # Вебхук для продакшена
        application.run_webhook(
            listen=config.WEBAPP_HOST,
            port=config.WEBAPP_PORT,
            url_path=config.BOT_TOKEN,
            webhook_url=f"{config.WEBHOOK_URL}/{config.BOT_TOKEN}"
        )
    else:
        # Локальный запуск
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()