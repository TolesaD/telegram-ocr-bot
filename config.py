import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'reminder_bot')
    
    # Webhook Configuration
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBAPP_HOST = os.getenv('WEBAPP_HOST', '0.0.0.0')
    WEBAPP_PORT = int(os.getenv('WEBAPP_PORT', 5000))
    
    # Admin ID (optional)
    ADMIN_ID = os.getenv('ADMIN_ID')