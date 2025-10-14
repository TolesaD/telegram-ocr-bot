import os

# Load .env file only in development (not in Railway production)
if not os.getenv('RAILWAY_ENVIRONMENT') and not os.getenv('RAILWAY_SERVICE_NAME'):
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Development mode: Loaded .env file")
else:
    print("🚀 Production mode: Using system environment variables")

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "ocr_bot"

# Enhanced Tesseract OCR Configuration
SUPPORTED_LANGUAGES = {
    'english': 'eng',
    'spanish': 'spa', 
    'french': 'fra',
    'german': 'deu',
    'italian': 'ita',
    'portuguese': 'por',
    'russian': 'rus',
    'chinese_simplified': 'chi_sim',
    'japanese': 'jpn',
    'korean': 'kor',
    'arabic': 'ara',
    'hindi': 'hin',
    'turkish': 'tur',
    'dutch': 'nld',
    'swedish': 'swe',
    'polish': 'pol',
    'ukrainian': 'ukr',
    'greek': 'ell',
}

# Language display names
LANGUAGE_DISPLAY_NAMES = {
    'english': 'English 🇺🇸',
    'spanish': 'Spanish 🇪🇸', 
    'french': 'French 🇫🇷',
    'german': 'German 🇩🇪',
    'italian': 'Italian 🇮🇹',
    'portuguese': 'Portuguese 🇵🇹',
    'russian': 'Russian 🇷🇺',
    'chinese_simplified': 'Chinese Simplified 🇨🇳',
    'japanese': 'Japanese 🇯🇵',
    'korean': 'Korean 🇰🇷',
    'arabic': 'Arabic 🇸🇦',
    'hindi': 'Hindi 🇮🇳',
    'turkish': 'Turkish 🇹🇷',
    'dutch': 'Dutch 🇳🇱',
    'swedish': 'Swedish 🇸🇪',
    'polish': 'Polish 🇵🇱',
    'ukrainian': 'Ukrainian 🇺🇦',
    'greek': 'Greek 🇬🇷',
}

# Language groups
LANGUAGE_GROUPS = {
    'popular': ['english', 'spanish', 'french', 'german', 'italian'],
    'european': ['portuguese', 'russian', 'dutch', 'swedish', 'polish', 'ukrainian', 'greek'],
    'asian': ['chinese_simplified', 'japanese', 'korean'],
    'middle_eastern': ['arabic', 'hindi', 'turkish']
}

# Performance Settings
MAX_IMAGE_SIZE = 15 * 1024 * 1024  # 15MB
PROCESSING_TIMEOUT = 30  # seconds
MAX_IMAGE_DIMENSION = 1200

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