const tg = window.Telegram.WebApp;
tg.expand();

let menuData;
let cart = [];

fetch("../menu.json")
  .then(r => r.json())
  .then(data => {
    menuData = data;
    showMenu();
  });

function showMenu() {
  const c = document.getElementById("content");
  c.innerHTML = "";

  Object.values(menuData).flat().forEach(i => {
    c.innerHTML += `
      <div class="card">
        <div>${i.name}<br>${i.price}₽</div>
        <input type="number" min="0" value="0"
          onchange="updateCart(${i.id}, '${i.name}', ${i.price}, this.value)">
      </div>
    `;
  });
}

function updateCart(id, name, price, qty) {
  cart = cart.filter(i => i.id !== id);
  if (qty > 0) cart.push({ id, name, price, qty: Number(qty) });
}

function submitOrder() {
  if (!cart.length) {
    tg.showAlert("Корзина пуста ☕");
    return;
  }

  tg.sendData(JSON.stringify({
    type: "Навынос",
    time: new Date().toLocaleTimeString(),
    items: cart
  }));

  tg.close();
}

function showProfile() {
  tg.showAlert("Профиль редактируется через бота 👤");
}

function showOrders() {
  tg.showAlert("История заказов доступна в боте 📦");
}
