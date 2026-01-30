import aiosqlite

DB = "coffee.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            items TEXT,
            total INTEGER,
            status TEXT,
            time TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        await db.commit()
