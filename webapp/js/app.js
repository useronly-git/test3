const tg = Telegram.WebApp;
tg.expand();

let cart = [];
let total = 0;

fetch("/menu.json")
.then(r => r.json())
.then(menu => {
  Object.values(menu).flat().forEach(i => {
    document.getElementById("menu").innerHTML += `
      <div class="card">
        <img src="${i.image}">
        <h3>${i.name}</h3>
        <p>${i.price} ₽</p>
        <button onclick="add('${i.id}', ${i.price})">Добавить</button>
      </div>
    `;
  });
});

function add(id, price){
  cart.push(id);
  total += price;
}

document.getElementById("checkout").onclick = () => {
  const time = prompt("К какому времени? (например 14:30)");
  tg.sendData(JSON.stringify({
    items: cart,
    total: total,
    time: time
  }));
};
