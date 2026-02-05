# backend/database.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import aiosqlite
import asyncio


class Database:
    def __init__(self, db_path='coffee_shop.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS users
                       (
                           user_id
                           INTEGER
                           PRIMARY
                           KEY,
                           username
                           TEXT,
                           first_name
                           TEXT,
                           last_name
                           TEXT,
                           name
                           TEXT,
                           phone
                           TEXT,
                           address
                           TEXT,
                           bonus_points
                           INTEGER
                           DEFAULT
                           0,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )
                       ''')

        # Таблица заказов
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS orders
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           user_id
                           INTEGER,
                           items
                           TEXT,
                           total_amount
                           REAL,
                           status
                           TEXT
                           DEFAULT
                           'new',
                           delivery_type
                           TEXT,
                           scheduled_time
                           TEXT,
                           address
                           TEXT,
                           notes
                           TEXT,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           FOREIGN
                           KEY
                       (
                           user_id
                       ) REFERENCES users
                       (
                           user_id
                       )
                           )
                       ''')

        conn.commit()
        conn.close()

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'name': row[4],
                    'phone': row[5],
                    'address': row[6],
                    'bonus_points': row[7],
                    'created_at': row[8]
                }
            return None

    async def create_user(self, user_id: int, username: str = None,
                          first_name: str = None, last_name: str = None):
        """Создать нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT
                OR IGNORE INTO users 
                (user_id, username, first_name, last_name) 
                VALUES (?, ?, ?, ?)''',
                (user_id, username, first_name, last_name)
            )
            await db.commit()

    async def update_user_profile(self, user_id: int, name: str = None,
                                  phone: str = None, address: str = None):
        """Обновить профиль пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            updates = []
            params = []

            if name:
                updates.append("name = ?")
                params.append(name)
            if phone:
                updates.append("phone = ?")
                params.append(phone)
            if address:
                updates.append("address = ?")
                params.append(address)

            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                await db.execute(query, params)
                await db.commit()

    async def create_order(self, user_id: int, items: List[Dict], total_amount: float,
                           delivery_type: str = 'pickup', scheduled_time: str = None,
                           address: str = None, notes: str = '') -> int:
        """Создать новый заказ"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                '''INSERT INTO orders
                   (user_id, items, total_amount, delivery_type, scheduled_time, address, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (user_id, json.dumps(items), total_amount, delivery_type,
                 scheduled_time, address, notes)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_order(self, order_id: int) -> Optional[Dict]:
        """Получить заказ по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM orders WHERE id = ?',
                (order_id,)
            )
            row = await cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'items': json.loads(row[2]),
                    'total_amount': row[3],
                    'status': row[4],
                    'delivery_type': row[5],
                    'scheduled_time': row[6],
                    'address': row[7],
                    'notes': row[8],
                    'created_at': row[9]
                }
            return None

    async def get_user_orders(self, user_id: int) -> List[Dict]:
        """Получить все заказы пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            rows = await cursor.fetchall()

            orders = []
            for row in rows:
                orders.append({
                    'id': row[0],
                    'user_id': row[1],
                    'items': json.loads(row[2]),
                    'total_amount': row[3],
                    'status': row[4],
                    'delivery_type': row[5],
                    'scheduled_time': row[6],
                    'address': row[7],
                    'notes': row[8],
                    'created_at': datetime.strptime(row[9], '%Y-%m-%d %H:%M:%S')
                })
            return orders

    async def update_order_status(self, order_id: int, status: str):
        """Обновить статус заказа"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE orders SET status = ? WHERE id = ?',
                (status, order_id)
            )
            await db.commit()