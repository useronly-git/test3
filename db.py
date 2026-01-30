import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from config import DB_PATH

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            tg_id INTEGER UNIQUE,
            name TEXT,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            items_json TEXT,
            total_price INTEGER,
            status TEXT,
            pickup_time TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            last_opened_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

def get_or_create_user(tg_id: int, name: Optional[str] = None) -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        row = c.fetchone()
        if row:
            return row["id"]
        c.execute(
            "INSERT INTO users (tg_id, name) VALUES (?, ?)",
            (tg_id, name or ""),
        )
        return c.lastrowid

def update_user_profile(tg_id: int, name: str, phone: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE users SET name = ?, phone = ? WHERE tg_id = ?",
            (name, phone, tg_id),
        )

def get_user_profile(tg_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        row = c.fetchone()
        return dict(row) if row else None

def create_order(user_id: int, items_json: str, total_price: int,
                 pickup_time: Optional[str], status: str = "new") -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO orders (user_id, items_json, total_price, status, pickup_time)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, items_json, total_price, status, pickup_time))
        return c.lastrowid

def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT * FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        """, (user_id,))
        rows = c.fetchall()
        return [dict(r) for r in rows]

def update_order_status(order_id: int, status: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = c.fetchone()
        return dict(row) if row else None
