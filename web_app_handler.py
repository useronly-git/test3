from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import json
from datetime import datetime, timedelta
from database import DatabaseManager, SessionLocal
import menu_data


class WebAppHandler:
    @staticmethod
    async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных из Web App"""
        data = json.loads(update.effective_message.web_app_data.data)
        action = data.get('action')
        telegram_id = update.effective_user.id

        db = SessionLocal()

        try:
            if action == 'create_order':
                await WebAppHandler._create_order(db, telegram_id, data, update, context)
            elif action == 'update_profile':
                await WebAppHandler._update_profile(db, telegram_id, data, update, context)
            elif action == 'add_to_cart':
                await WebAppHandler._add_to_cart(db, telegram_id, data, update, context)
            elif action == 'clear_cart':
                await WebAppHandler._clear_cart(db, telegram_id, update, context)

        except Exception as e:
            await update.effective_message.reply_text(
                f"Произошла ошибка: {str(e)}"
            )
        finally:
            db.close()

    @staticmethod
    async def _create_order(db, telegram_id, data, update, context):
        """Создание заказа"""
        items = data.get('items', [])
        order_type = data.get('order_type', 'takeaway')
        delivery_time = data.get('delivery_time')
        address = data.get('address')
        notes = data.get('notes', '')
        payment_method = data.get('payment_method', 'cash')

        # Расчет общей суммы
        total_amount = 0
        for item in items:
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            total_amount += price * quantity

            # Добавляем стоимость дополнений
            for addon in item.get('addons', []):
                addon_price = menu_data.ADDONS.get(addon, 0)
                total_amount += addon_price

        if delivery_time:
            delivery_time = datetime.fromisoformat(delivery_time)

        # Создание заказа в БД
        order = DatabaseManager.create_order(
            db=db,
            telegram_id=telegram_id,
            items=items,
            total_amount=total_amount,
            order_type=order_type,
            delivery_time=delivery_time,
            address=address,
            notes=notes,
            payment_method=payment_method
        )

        # Отправка подтверждения клиенту
        order_text = (
            f"✅ Заказ #{order.order_number} оформлен!\n\n"
            f"💰 Сумма: {total_amount} руб.\n"
            f"📦 Тип: {'Навынос' if order_type == 'takeaway' else 'На месте'}\n"
            f"📅 Время: {delivery_time.strftime('%d.%m.%Y %H:%M') if delivery_time else 'Как можно скорее'}\n"
            f"📍 Адрес: {address if address else 'Самовывоз из кофейни'}\n"
            f"📝 Примечания: {notes if notes else 'Нет'}\n\n"
            f"Статус заказа можно отслеживать в разделе 'Мои заказы'."
        )

        await update.effective_message.reply_text(order_text)

        # Отправка заказа в чат админа с кнопками статусов
        admin_keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_order_{order.id}"),
                InlineKeyboardButton("👨‍🍳 Готовится", callback_data=f"preparing_order_{order.id}")
            ],
            [
                InlineKeyboardButton("📦 Готов к выдаче", callback_data=f"ready_order_{order.id}"),
                InlineKeyboardButton("✅ Выполнен", callback_data=f"complete_order_{order.id}")
            ],
            [
                InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_order_{order.id}")
            ]
        ]

        admin_message = (
            f"🆕 Новый заказ #{order.order_number}\n"
            f"👤 Клиент: @{update.effective_user.username}\n"
            f"📞 ID: {telegram_id}\n"
            f"💰 Сумма: {total_amount} руб.\n"
            f"📦 Тип: {'Навынос' if order_type == 'takeaway' else 'На месте'}\n"
            f"📍 Адрес: {address if address else 'Самовывоз'}\n\n"
            f"Товары:\n"
        )

        for item in items:
            admin_message += f"• {item.get('name')} x{item.get('quantity')} - {item.get('price')} руб.\n"

        # Отправка всем админам
        for admin_id in context.bot_data.get('admin_ids', []):
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    reply_markup=InlineKeyboardMarkup(admin_keyboard)
                )
            except:
                pass

    @staticmethod
    async def _update_profile(db, telegram_id, data, update, context):
        """Обновление профиля пользователя"""
        user_data = {
            'phone': data.get('phone'),
            'email': data.get('email'),
            'address': data.get('address')
        }

        user = DatabaseManager.update_user_profile(db, telegram_id, **user_data)

        await update.effective_message.reply_text(
            "✅ Профиль успешно обновлен!"
        )

    @staticmethod
    async def _add_to_cart(db, telegram_id, data, update, context):
        """Добавление товара в корзину"""
        cart = DatabaseManager.get_cart(db, telegram_id)
        new_item = data.get('item')

        # Проверяем, есть ли уже такой товар в корзине
        for item in cart.items:
            if (item.get('id') == new_item.get('id') and
                    item.get('size') == new_item.get('size') and
                    item.get('addons') == new_item.get('addons')):
                item['quantity'] = item.get('quantity', 1) + 1
                break
        else:
            new_item['quantity'] = 1
            cart.items.append(new_item)

        DatabaseManager.update_cart(db, telegram_id, cart.items)

        await update.effective_message.reply_text(
            f"✅ {new_item.get('name')} добавлен в корзину!"
        )

    @staticmethod
    async def _clear_cart(db, telegram_id, update, context):
        """Очистка корзины"""
        DatabaseManager.update_cart(db, telegram_id, [])

        await update.effective_message.reply_text(
            "🗑️ Корзина очищена!"
        )