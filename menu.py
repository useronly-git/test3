from dataclasses import dataclass
from typing import List

@dataclass
class MenuItem:
    id: int
    name: str
    description: str
    price: int  # в копейках/центах
    category: str

MENU_ITEMS: List[MenuItem] = [
    MenuItem(
        id=1,
        name="Эспрессо",
        description="Классический эспрессо, 30 мл",
        price=800,
        category="Кофе",
    ),
    MenuItem(
        id=2,
        name="Капучино",
        description="С молоком, 250 мл",
        price=1200,
        category="Кофе",
    ),
    MenuItem(
        id=3,
        name="Флэт уайт",
        description="Плотный молочный кофе, 200 мл",
        price=1400,
        category="Кофе",
    ),
    MenuItem(
        id=4,
        name="Чизкейк",
        description="Классический чизкейк, порция",
        price=1800,
        category="Десерты",
    ),
]

def get_menu():
    return MENU_ITEMS

def get_item_by_id(item_id: int) -> MenuItem | None:
    for item in MENU_ITEMS:
        if item.id == item_id:
            return item
    return None
