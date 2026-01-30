import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен бота
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")  # URL mini app
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # чат/группа для заказов

DB_PATH = os.getenv("DB_PATH", "coffee.db")
