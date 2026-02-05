// frontend/app.js
class CoffeeShopApp {
    constructor() {
        this.menu = null;
        this.cart = [];
        this.currentCategory = null;
        this.userId = this.getUserId();

        this.init();
    }

    getUserId() {
        // Получаем user_id из URL
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || 'guest';

        // Проверяем, если это режим заказа ко времени
        const scheduled = urlParams.get('scheduled');
        if (scheduled === 'true') {
            // Показываем опции времени при оформлении
            setTimeout(() => {
                document.getElementById('scheduledTime').value = 'custom';
                document.getElementById('customTimeGroup').style.display = 'block';
            }, 1000);
        }

        return userId;
    }

    async init() {
        await this.loadMenu();
        this.setupEventListeners();
        this.renderCategories();
        this.updateCartCount();
    }

    async loadMenu() {
        try {
            const response = await fetch('menu.json');
            this.menu = await response.json();
            this.renderProducts();
        } catch (error) {
            console.error('Error loading menu:', error);
            this.showNotification('Ошибка загрузки меню', 'error');
        }
    }

    setupEventListeners() {
        // Корзина
        document.getElementById('cartIcon').addEventListener('click', () => this.toggleCart());
        document.getElementById('closeCart').addEventListener('click', () => this.toggleCart());

        // Оформление заказа
        document.getElementById('checkoutBtn').addEventListener('click', () => this.openCheckoutModal());
        document.getElementById('confirmOrder').addEventListener('click', () => this.confirmOrder());

        // Закрытие модальных окон
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(modal => {
                    modal.classList.remove('active');
                });
            });
        });

        // Клик вне модального окна
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Выбор времени заказа
        document.getElementById('scheduledTime').addEventListener('change', (e) => {
            const customTimeGroup = document.getElementById('customTimeGroup');
            customTimeGroup.style.display = e.target.value === 'custom' ? 'block' : 'none';
        });

        // Тип получения
        document.getElementById('deliveryType').addEventListener('change', (e) => {
            const addressGroup = document.getElementById('addressGroup');
            if (e.target.value === 'dine_in') {
                addressGroup.querySelector('input').placeholder = 'Номер столика (если требуется)';
            } else {
                addressGroup.querySelector('input').placeholder = 'Укажите адрес';
            }
        });
    }

    renderCategories() {
        const container = document.getElementById('categories');
        container.innerHTML = '';

        this.menu.categories.forEach(category => {
            const button = document.createElement('button');
            button.className = 'category-btn';
            button.textContent = category.name;
            button.dataset.categoryId = category.id;

            button.addEventListener('click', () => {
                document.querySelectorAll('.category-btn').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                this.currentCategory = category.id;
                this.renderProducts();
            });

            container.appendChild(button);
        });

        // Активируем первую категорию
        if (this.menu.categories.length > 0 && !this.currentCategory) {
            container.querySelector('.category-btn').click();
        }
    }

    renderProducts() {
        const container = document.getElementById('products');
        container.innerHTML = '';

        const category = this.menu.categories.find(cat => cat.id === this.currentCategory);
        if (!category) return;

        category.items.forEach(item => {
            const card = this.createProductCard(item);
            container.appendChild(card);
        });
    }

    createProductCard(item) {
        const card = document.createElement('div');
        card.className = 'product-card';

        const inCart = this.cart.find(cartItem => cartItem.id === item.id);

        card.innerHTML = `
            <div class="product-image">
                <i class="fas fa-mug-hot"></i>
            </div>
            <div class="product-info">
                <h3 class="product-name">${item.name}</h3>
                <p class="product-description">${item.description}</p>
                <div class="product-price">${item.price} руб.</div>
                <button class="btn-add-to-cart">
                    ${inCart ? `В корзине (${inCart.quantity})` : 'Добавить в корзину'}
                </button>
            </div>
        `;

        const addToCartBtn = card.querySelector('.btn-add-to-cart');
        addToCartBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.addToCart(item);
            this.updateProductCard(card, item);
        });

        card.addEventListener('click', () => {
            this.openProductModal(item);
        });

        return card;
    }

    updateProductCard(card, item) {
        const inCart = this.cart.find(cartItem => cartItem.id === item.id);
        const button = card.querySelector('.btn-add-to-cart');

        if (inCart) {
            button.textContent = `В корзине (${inCart.quantity})`;
            button.style.backgroundColor = '#4caf50';
        } else {
            button.textContent = 'Добавить в корзину';
            button.style.backgroundColor = '';
        }
    }

    openProductModal(item) {
        const modal = document.getElementById('productModal');
        const modalBody = document.getElementById('modalBody');

        let optionsHtml = '';
        if (item.options) {
            item.options.forEach(option => {
                optionsHtml += `
                    <div class="form-group">
                        <label>${option.name}:</label>
                        <select class="form-control option-select" data-option="${option.name}">
                            ${option.choices.map(choice => `<option value="${choice}">${choice}</option>`).join('')}
                        </select>
                    </div>
                `;
            });
        }

        modalBody.innerHTML = `
            <h2>${item.name}</h2>
            <p class="modal-description">${item.description}</p>
            <div class="modal-price">${item.price} руб.</div>
            
            ${optionsHtml}
            
            <div class="modal-actions">
                <button class="btn btn-primary" id="modalAddToCart">Добавить в корзину</button>
            </div>
        `;

        document.getElementById('modalAddToCart').addEventListener('click', () => {
            const options = {};
            document.querySelectorAll('.option-select').forEach(select => {
                options[select.dataset.option] = select.value;
            });

            this.addToCart({...item, selectedOptions: options});
            this.showNotification(`${item.name} добавлен в корзину`);
            modal.classList.remove('active');
        });

        modal.classList.add('active');
    }

    addToCart(item) {
        const existingItem = this.cart.find(cartItem => cartItem.id === item.id);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                ...item,
                quantity: 1,
                selectedOptions: item.selectedOptions || {}
            });
        }

        this.updateCartCount();
        this.renderCart();
        this.saveCart();
    }

    removeFromCart(itemId) {
        this.cart = this.cart.filter(item => item.id !== itemId);
        this.updateCartCount();
        this.renderCart();
        this.saveCart();
    }

    updateQuantity(itemId, newQuantity) {
        if (newQuantity < 1) {
            this.removeFromCart(itemId);
            return;
        }

        const item = this.cart.find(cartItem => cartItem.id === itemId);
        if (item) {
            item.quantity = newQuantity;
            this.updateCartCount();
            this.renderCart();
            this.saveCart();
        }
    }

    updateCartCount() {
        const count = this.cart.reduce((total, item) => total + item.quantity, 0);
        document.getElementById('cartCount').textContent = count;
    }

    toggleCart() {
        document.getElementById('cartSidebar').classList.toggle('active');
    }

    renderCart() {
        const container = document.getElementById('cartItems');
        container.innerHTML = '';

        if (this.cart.length === 0) {
            container.innerHTML = '<p class="empty-cart">Корзина пуста</p>';
            return;
        }

        this.cart.forEach(item => {
            const cartItem = document.createElement('div');
            cartItem.className = 'cart-item';

            const totalPrice = item.price * item.quantity;

            let optionsText = '';
            if (item.selectedOptions && Object.keys(item.selectedOptions).length > 0) {
                optionsText = Object.entries(item.selectedOptions)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(', ');
            }

            cartItem.innerHTML = `
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.name}</div>
                    ${optionsText ? `<div class="cart-item-options">${optionsText}</div>` : ''}
                    <div class="cart-item-price">${totalPrice} руб.</div>
                </div>
                <div class="cart-item-controls">
                    <button class="btn-quantity decrease" data-id="${item.id}">-</button>
                    <span class="cart-item-quantity">${item.quantity}</span>
                    <button class="btn-quantity increase" data-id="${item.id}">+</button>
                    <button class="btn-quantity remove" data-id="${item.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;

            container.appendChild(cartItem);
        });

        // Добавляем обработчики событий для кнопок в корзине
        container.querySelectorAll('.decrease').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = parseInt(e.target.dataset.id);
                const item = this.cart.find(cartItem => cartItem.id === itemId);
                if (item) {
                    this.updateQuantity(itemId, item.quantity - 1);
                }
            });
        });

        container.querySelectorAll('.increase').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = parseInt(e.target.dataset.id);
                const item = this.cart.find(cartItem => cartItem.id === itemId);
                if (item) {
                    this.updateQuantity(itemId, item.quantity + 1);
                }
            });
        });

        container.querySelectorAll('.remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = parseInt(e.target.dataset.id);
                this.removeFromCart(itemId);
            });
        });

        // Обновляем итоговую сумму
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        document.getElementById('cartTotal').textContent = `${total} руб.`;
        document.getElementById('orderTotal').textContent = total;
    }

    saveCart() {
        localStorage.setItem('coffeeShopCart', JSON.stringify(this.cart));
    }

    loadCart() {
        const savedCart = localStorage.getItem('coffeeShopCart');
        if (savedCart) {
            this.cart = JSON.parse(savedCart);
            this.updateCartCount();
            this.renderCart();
        }
    }

    openCheckoutModal() {
        if (this.cart.length === 0) {
            this.showNotification('Корзина пуста', 'error');
            return;
        }

        // Загружаем сохраненные данные
        const savedDelivery = localStorage.getItem('deliveryType') || 'pickup';
        const savedAddress = localStorage.getItem('address') || '';
        const savedNotes = localStorage.getItem('notes') || '';

        document.getElementById('deliveryType').value = savedDelivery;
        document.getElementById('address').value = savedAddress;
        document.getElementById('notes').value = savedNotes;

        // Рассчитываем итоговую сумму
        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        document.getElementById('orderTotal').textContent = total;

        document.getElementById('checkoutModal').classList.add('active');
        this.toggleCart();
    }

    async confirmOrder() {
        if (this.cart.length === 0) {
            this.showNotification('Корзина пуста', 'error');
            return;
        }

        const deliveryType = document.getElementById('deliveryType').value;
        const address = document.getElementById('address').value;
        let scheduledTime = document.getElementById('scheduledTime').value;
        const notes = document.getElementById('notes').value;

        // Обработка времени заказа
        if (scheduledTime === 'custom') {
            const customTime = document.getElementById('customTime').value;
            if (!customTime) {
                this.showNotification('Укажите время заказа', 'error');
                return;
            }
            scheduledTime = customTime;
        } else if (scheduledTime === 'now') {
            scheduledTime = 'Как можно скорее';
        } else if (scheduledTime === '30min') {
            scheduledTime = 'Через 30 минут';
        } else if (scheduledTime === '1hour') {
            scheduledTime = 'Через 1 час';
        }

        // Сохраняем данные для будущих заказов
        localStorage.setItem('deliveryType', deliveryType);
        localStorage.setItem('address', address);
        localStorage.setItem('notes', notes);

        // Подготавливаем данные заказа
        const orderData = {
            user_id: this.userId,
            items: this.cart.map(item => ({
                id: item.id,
                name: item.name,
                price: item.price,
                quantity: item.quantity,
                options: item.selectedOptions
            })),
            total: this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0),
            delivery_type: deliveryType,
            scheduled_time: scheduledTime,
            address: address,
            notes: notes
        };

        try {
            // Отправляем данные в Telegram
            if (window.Telegram && Telegram.WebApp) {
                Telegram.WebApp.sendData(JSON.stringify(orderData));
                this.showNotification('Заказ успешно оформлен!');

                // Очищаем корзину
                this.cart = [];
                this.updateCartCount();
                this.renderCart();
                this.saveCart();

                // Закрываем модальное окно
                document.getElementById('checkoutModal').classList.remove('active');

                // Закрываем мини-приложение через 3 секунды
                setTimeout(() => {
                    if (window.Telegram && Telegram.WebApp) {
                        Telegram.WebApp.close();
                    }
                }, 3000);
            } else {
                // Для тестирования вне Telegram
                console.log('Order data:', orderData);
                this.showNotification('Заказ оформлен (тестовый режим)');

                this.cart = [];
                this.updateCartCount();
                this.renderCart();
                this.saveCart();

                document.getElementById('checkoutModal').classList.remove('active');
            }
        } catch (error) {
            console.error('Error sending order:', error);
            this.showNotification('Ошибка при оформлении заказа', 'error');
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = 'notification';

        if (type === 'error') {
            notification.classList.add('error');
        }

        notification.style.display = 'block';

        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
}

// Инициализация приложения
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new CoffeeShopApp();

    // Загружаем корзину из localStorage
    app.loadCart();

    // Инициализация Telegram Web App
    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.ready();
        Telegram.WebApp.expand();
    }
});