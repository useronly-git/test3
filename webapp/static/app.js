let cart = {};

function recalcTotal() {
    let total = 0;
    document.querySelectorAll(".qty-input").forEach(input => {
        const qty = parseInt(input.value) || 0;
        const id = parseInt(input.dataset.id);
        const card = input.closest(".card");
        const priceText = card.querySelector(".fw-bold").innerText.replace(" ₽", "").replace(",", ".");
        const price = parseFloat(priceText) * 100;
        if (qty > 0) {
            total += qty * price;
            cart[id] = qty;
        } else {
            delete cart[id];
        }
    });
    document.getElementById("totalPrice").innerText = (total / 100).toFixed(2);
}

document.addEventListener("click", (e) => {
    if (e.target.classList.contains("qty-plus")) {
        const id = e.target.dataset.id;
        const input = document.querySelector(`.qty-input[data-id="${id}"]`);
        input.value = (parseInt(input.value) || 0) + 1;
        recalcTotal();
    }
    if (e.target.classList.contains("qty-minus")) {
        const id = e.target.dataset.id;
        const input = document.querySelector(`.qty-input[data-id="${id}"]`);
        input.value = Math.max(0, (parseInt(input.value) || 0) - 1);
        recalcTotal();
    }
});

async function loadProfile() {
    if (!TG_ID) return;
    const res = await fetch(`/api/profile?tg_id=${TG_ID}`);
    const data = await res.json();
    document.getElementById("profileName").value = data.name || "";
    document.getElementById("profilePhone").value = data.phone || "";
}

async function saveProfile(e) {
    e.preventDefault();
    if (!TG_ID) return;
    const body = {
        name: document.getElementById("profileName").value,
        phone: document.getElementById("profilePhone").value,
    };
    await fetch(`/api/profile?tg_id=${TG_ID}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
    });
    alert("Профиль сохранён");
}

async function loadOrders() {
    if (!TG_ID) return;
    const res = await fetch(`/api/orders?tg_id=${TG_ID}`);
    const data = await res.json();
    const container = document.getElementById("ordersList");
    container.innerHTML = "";
    if (!data.length) {
        container.innerHTML = "<p>Заказов пока нет.</p>";
        return;
    }
    data.forEach(o => {
        const div = document.createElement("div");
        div.className = "card mb-2";
        div.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <div class="fw-bold">Заказ #${o.id}</div>
                        <div class="text-muted">Статус: ${o.status}</div>
                        ${o.pickup_time ? `<div class="text-muted">Ко времени: ${o.pickup_time}</div>` : ""}
                    </div>
                    <div class="fw-bold">${(o.total_price / 100).toFixed(2)} ₽</div>
                </div>
            </div>
        `;
        container.appendChild(div);
    });
}

async function createOrder() {
    if (!TG_ID) {
        alert("tg_id не передан. Откройте mini app из Telegram.");
        return;
    }
    const items = Object.entries(cart).map(([id, qty]) => ({
        id: parseInt(id),
        qty: parseInt(qty),
    }));
    if (!items.length) {
        alert("Добавьте позиции в заказ.");
        return;
    }
    const pickupTime = document.getElementById("pickupTime").value || null;
    const body = { tg_id: TG_ID, items, pickup_time: pickupTime };
    const res = await fetch("/api/create_order", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.status === "ok") {
        alert(`Заказ #${data.order_id} оформлен!`);
        cart = {};
        document.querySelectorAll(".qty-input").forEach(i => i.value = 0);
        recalcTotal();
        loadOrders();
    } else {
        alert("Ошибка при оформлении заказа");
    }
}

document.getElementById("profileForm").addEventListener("submit", saveProfile);
document.getElementById("btnCreateOrder").addEventListener("click", createOrder);

document.addEventListener("DOMContentLoaded", () => {
    recalcTotal();
    loadProfile();
    loadOrders();
});
