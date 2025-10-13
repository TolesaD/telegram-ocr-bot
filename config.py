import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "ocr_bot"

# Languages available on PythonAnywhere
SUPPORTED_LANGUAGES = {
    'english': 'eng',
    'spanish': 'spa', 
    'french': 'fra',
    'german': 'deu',
    'italian': 'ita',
    'portuguese': 'por',
    'russian': 'rus',
    'dutch': 'nld',
    'turkish': 'tur',
    # African languages are typically NOT available on PythonAnywhere free tier
    # 'amharic': 'amh',
    # 'afrikaans': 'afr', 
    # 'swahili': 'swa',
}

LANGUAGE_DISPLAY_NAMES = {
    'english': 'English 🇺🇸',
    'spanish': 'Spanish 🇪🇸', 
    'french': 'French 🇫🇷',
    'german': 'German 🇩🇪',
    'italian': 'Italian 🇮🇹',
    'portuguese': 'Portuguese 🇵🇹',
    'russian': 'Russian 🇷🇺',
    'dutch': 'Dutch 🇳🇱',
    'turkish': 'Turkish 🇹🇷',
}

# Language groups - only include available languages
LANGUAGE_GROUPS = {
    'european': ['english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'russian', 'dutch'],
    'other': ['turkish'],
}

# Remove empty groups
LANGUAGE_GROUPS = {k: v for k, v in LANGUAGE_GROUPS.items() if v}

# Performance Settings
MAX_IMAGE_SIZE = 8 * 1024 * 1024
PROCESSING_TIMEOUT = 30
MAX_IMAGE_DIMENSION = 1600

# Text Formatting Options
FORMAT_OPTIONS = ['plain', 'markdown', 'html']

# Support Email
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'tolesadebushe9@gmail.com')

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