from flask import Flask, render_template, request, jsonify
from menu import get_menu, get_item_by_id
from db import (
    get_or_create_user, update_user_profile, get_user_profile,
    create_order, get_user_orders
)
import json

app = Flask(__name__)

@app.route("/")
def index():
    # Telegram WebApp передаёт initData, но для простоты
    # будем принимать tg_id через query-параметр в тестах
    tg_id = request.args.get("tg_id", type=int)
    return render_template("index.html", tg_id=tg_id, menu=get_menu())

@app.route("/api/profile", methods=["GET", "POST"])
def profile():
    tg_id = int(request.args.get("tg_id"))
    if request.method == "GET":
        profile = get_user_profile(tg_id)
        if not profile:
            user_id = get_or_create_user(tg_id)
            profile = get_user_profile(tg_id)
        return jsonify(profile)
    else:
        data = request.json
        name = data.get("name", "")
        phone = data.get("phone", "")
        update_user_profile(tg_id, name, phone)
        return jsonify({"status": "ok"})

@app.route("/api/orders", methods=["GET"])
def orders():
    tg_id = int(request.args.get("tg_id"))
    profile = get_user_profile(tg_id)
    if not profile:
        return jsonify([])
    orders = get_user_orders(profile["id"])
    return jsonify(orders)

@app.route("/api/create_order", methods=["POST"])
def create_order_api():
    data = request.json
    tg_id = int(data["tg_id"])
    items = data["items"]  # [{id, qty}, ...]
    pickup_time = data.get("pickup_time")

    profile = get_user_profile(tg_id)
    if not profile:
        user_id = get_or_create_user(tg_id)
        profile = get_user_profile(tg_id)

    total_price = 0
    detailed_items = []
    for item in items:
        menu_item = get_item_by_id(item["id"])
        if not menu_item:
            continue
        qty = int(item["qty"])
        total_price += menu_item.price * qty
        detailed_items.append({
            "id": menu_item.id,
            "name": menu_item.name,
            "qty": qty,
            "price": menu_item.price,
        })

    order_id = create_order(
        user_id=profile["id"],
        items_json=json.dumps(detailed_items, ensure_ascii=False),
        total_price=total_price,
        pickup_time=pickup_time,
        status="new"
    )

    # здесь можно отправить заказ в ADMIN_CHAT_ID через Bot API (HTTP запросом)
    # или через отдельный сервис

    return jsonify({"status": "ok", "order_id": order_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
