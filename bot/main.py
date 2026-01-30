import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import start, webapp, admin

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(webapp.router)
dp.include_router(admin.router)

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
