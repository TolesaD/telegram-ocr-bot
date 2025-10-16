import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Performance Settings
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB for Railway
PROCESSING_TIMEOUT = 45  # seconds

# Text Formatting Options (replaced markdown with copiable)
FORMAT_OPTIONS = ['plain', 'html', 'copiable']

# Support Bot
SUPPORT_BOT = os.getenv('SUPPORT_BOT', '@ImageToTextConvertorSupportBot')

# Channel Configuration
ANNOUNCEMENT_CHANNEL = "@ImageToTextConverter"
CHANNEL_USERNAME = "ImageToTextConverter"

# Admin User IDs
admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = []
if admin_ids_str:
    for admin_id in admin_ids_str.split(','):
        admin_id = admin_id.strip()
        if admin_id and admin_id.isdigit():
            ADMIN_IDS.append(int(admin_id))

# Railway environment
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None