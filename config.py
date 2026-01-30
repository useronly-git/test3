import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(',')))
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 8080
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///coffee_shop.db")