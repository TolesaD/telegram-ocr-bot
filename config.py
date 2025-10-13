import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "ocr_bot"

# Enhanced Tesseract OCR Configuration with Multiple Languages including African
SUPPORTED_LANGUAGES = {
    # European Languages
    'english': 'eng',
    'spanish': 'spa',
    'french': 'fra',
    'german': 'deu',
    'italian': 'ita',
    'portuguese': 'por',
    'russian': 'rus',
    'dutch': 'nld',
    'swedish': 'swe',
    'polish': 'pol',
    'ukrainian': 'ukr',
    'greek': 'ell',
    
    # Asian Languages
    'chinese_simplified': 'chi_sim',
    'japanese': 'jpn',
    'korean': 'kor',
    'thai': 'tha',
    'vietnamese': 'vie',
    
    # Middle Eastern Languages
    'arabic': 'ara',
    'hebrew': 'heb',
    'turkish': 'tur',
    'persian': 'fas',
    
    # African Languages
    'amharic': 'amh',
    'afrikaans': 'afr',
    'swahili': 'swa',
    'yoruba': 'yor',
    'hausa': 'hau',
    'igbo': 'ibo',
    'somali': 'som',
    'zulu': 'zul',
    'xhosa': 'xho',
    
    # Indian Languages
    'hindi': 'hin',
    'bengali': 'ben',
    'tamil': 'tam',
    'telugu': 'tel',
    'marathi': 'mar',
    'urdu': 'urd',
    'gujarati': 'guj',
    'punjabi': 'pan'
}

# Language display names for the menu
LANGUAGE_DISPLAY_NAMES = {
    # European
    'english': 'English 🇺🇸',
    'spanish': 'Spanish 🇪🇸', 
    'french': 'French 🇫🇷',
    'german': 'German 🇩🇪',
    'italian': 'Italian 🇮🇹',
    'portuguese': 'Portuguese 🇵🇹',
    'russian': 'Russian 🇷🇺',
    'dutch': 'Dutch 🇳🇱',
    'swedish': 'Swedish 🇸🇪',
    'polish': 'Polish 🇵🇱',
    'ukrainian': 'Ukrainian 🇺🇦',
    'greek': 'Greek 🇬🇷',
    
    # Asian
    'chinese_simplified': 'Chinese Simplified 🇨🇳',
    'japanese': 'Japanese 🇯🇵',
    'korean': 'Korean 🇰🇷',
    'thai': 'Thai 🇹🇭',
    'vietnamese': 'Vietnamese 🇻🇳',
    
    # Middle Eastern
    'arabic': 'Arabic 🇸🇦',
    'hebrew': 'Hebrew 🇮🇱',
    'turkish': 'Turkish 🇹🇷',
    'persian': 'Persian 🇮🇷',
    
    # African Languages
    'amharic': 'Amharic 🇪🇹',
    'afrikaans': 'Afrikaans 🇿🇦',
    'swahili': 'Swahili 🇰🇪',
    'yoruba': 'Yoruba 🇳🇬',
    'hausa': 'Hausa 🇳🇬',
    'igbo': 'Igbo 🇳🇬',
    'somali': 'Somali 🇸🇴',
    'zulu': 'Zulu 🇿🇦',
    'xhosa': 'Xhosa 🇿🇦',
    
    # Indian
    'hindi': 'Hindi 🇮🇳',
    'bengali': 'Bengali 🇧🇩',
    'tamil': 'Tamil 🇮🇳',
    'telugu': 'Telugu 🇮🇳',
    'marathi': 'Marathi 🇮🇳',
    'urdu': 'Urdu 🇵🇰',
    'gujarati': 'Gujarati 🇮🇳',
    'punjabi': 'Punjabi 🇮🇳'
}

# Language groups for better menu organization
LANGUAGE_GROUPS = {
    'european': ['english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'russian', 'dutch', 'swedish', 'polish', 'ukrainian', 'greek'],
    'asian': ['chinese_simplified', 'japanese', 'korean', 'thai', 'vietnamese'],
    'middle_eastern': ['arabic', 'hebrew', 'turkish', 'persian'],
    'african': ['amharic', 'afrikaans', 'swahili', 'yoruba', 'hausa', 'igbo', 'somali', 'zulu', 'xhosa'],  # NEW GROUP
    'indian': ['hindi', 'bengali', 'tamil', 'telugu', 'marathi', 'urdu', 'gujarati', 'punjabi'],
    'other': []  # Empty for now
}

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