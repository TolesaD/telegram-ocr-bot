import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enhanced language support
SUPPORTED_LANGUAGES = {
    'english': 'eng', 'spanish': 'spa', 'french': 'fra', 'german': 'deu',
    'italian': 'ita', 'portuguese': 'por', 'russian': 'rus', 
    'chinese_simplified': 'chi_sim', 'japanese': 'jpn', 'korean': 'kor',
    'arabic': 'ara', 'hindi': 'hin', 'turkish': 'tur', 'dutch': 'nld',
    'swedish': 'swe', 'polish': 'pol', 'ukrainian': 'ukr', 'greek': 'ell',
    'amharic': 'amh'
}

# Performance Settings
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB for Railway
PROCESSING_TIMEOUT = 45  # seconds

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

# Railway environment
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None