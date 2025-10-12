import os
from dotenv import load_dotenv

load_dotenv()

# Remove the Config class and use direct variables
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "reminder_bot"

# Tesseract OCR Configuration
SUPPORTED_LANGUAGES = {
    'english': 'eng',
    # Comment out languages you don't have installed
    # 'spanish': 'spa',
    # 'french': 'fra',
    # 'german': 'deu',
    # 'italian': 'ita',
    # 'portuguese': 'por',
    # 'russian': 'rus',
    # 'chinese': 'chi_sim',
    # 'japanese': 'jpn',
    # 'korean': 'kor',
    # 'arabic': 'ara',
    # 'hindi': 'hin'
}

# Text Formatting Options
FORMAT_OPTIONS = ['plain', 'markdown', 'html']

# Support Email
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'tolesadebushe9@gmail.com')

# Admin User IDs (optional)
admin_ids_str = os.getenv('ADMIN_IDS', '')
# Safely parse ADMIN_IDS
ADMIN_IDS = []
if admin_ids_str:
    for admin_id in admin_ids_str.split(','):
        admin_id = admin_id.strip()
        if admin_id and admin_id.isdigit():
            ADMIN_IDS.append(int(admin_id))