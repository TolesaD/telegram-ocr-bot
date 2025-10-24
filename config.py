# config.py
import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8327516444:AAGblijJShx3Uh9cWU7coADtUl_PnAeDZ5A')
SUPPORT_BOT = os.getenv('SUPPORT_BOT', '@ImageToTextConverterSupportBot')
CHANNEL_USERNAME = os.getenv('CHANNEL', '@ImageToTextConverter')
ANNOUNCEMENT_CHANNEL = os.getenv('CHANNEL', '@ImageToTextConverter')  # Use the same for now
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '417079598').split(',')]

# OCR Configuration
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
PROCESSING_TIMEOUT = 120  # seconds

# Format Options
FORMAT_OPTIONS = ['plain', 'html']

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///ocr_bot.db')

# Feature Flags
ENABLE_AMHARIC = True
ENABLE_MULTILINGUAL = True
ENABLE_STATISTICS = True