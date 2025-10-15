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

# Language display names
LANGUAGE_DISPLAY_NAMES = {
    'english': 'English 🇺🇸', 'spanish': 'Spanish 🇪🇸', 'french': 'French 🇫🇷',
    'german': 'German 🇩🇪', 'italian': 'Italian 🇮🇹', 'portuguese': 'Portuguese 🇵🇹',
    'russian': 'Russian 🇷🇺', 'chinese_simplified': 'Chinese 🇨🇳',
    'japanese': 'Japanese 🇯🇵', 'korean': 'Korean 🇰🇷', 'arabic': 'Arabic 🇸🇦',
    'hindi': 'Hindi 🇮🇳', 'turkish': 'Turkish 🇹🇷', 'dutch': 'Dutch 🇳🇱',
    'swedish': 'Swedish 🇸🇪', 'polish': 'Polish 🇵🇱', 'ukrainian': 'Ukrainian 🇺🇦',
    'greek': 'Greek 🇬🇷', 'amharic': 'Amharic 🇪🇹'
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

# Railway-specific settings
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None