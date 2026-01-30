const tg = window.Telegram.WebApp;
tg.expand();

fetch("../menu.json")
  .then(r => r.json())
  .then(menu => {
    const root = document.getElementById("menu");
    Object.keys(menu).forEach(cat => {
      root.innerHTML += `<h2>${cat}</h2>`;
      menu[cat].forEach(i => {
        root.innerHTML += `
          <div>
            ${i.name} — ${i.price}₽
            <input type="number" min="0" value="0" id="item_${i.id}">
          </div>`;
      });
    });
  });

function submitOrder() {
  tg.sendData("ORDER_SUBMITTED");
  tg.close();
}
