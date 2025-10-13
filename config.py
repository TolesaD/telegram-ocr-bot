import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "ocr_bot"

# Enhanced Tesseract OCR Configuration with INSTALLED languages only
# Remove languages that aren't installed on your system
SUPPORTED_LANGUAGES = {
    # European Languages (usually installed by default)
    'english': 'eng',
    'spanish': 'spa',
    'french': 'fra',
    'german': 'deu',
    'italian': 'ita',
    'portuguese': 'por',
    
    # Comment out languages you don't have installed
    # 'russian': 'rus',
    # 'dutch': 'nld',
    # 'swedish': 'swe',
    # 'polish': 'pol',
    # 'ukrainian': 'ukr',
    # 'greek': 'ell',
    
    # Asian Languages
    # 'chinese_simplified': 'chi_sim',
    # 'japanese': 'jpn',
    # 'korean': 'kor',
    # 'thai': 'tha',
    # 'vietnamese': 'vie',
    
    # Middle Eastern Languages
    # 'arabic': 'ara',
    # 'hebrew': 'heb',
    # 'turkish': 'tur',
    # 'persian': 'fas',
    
    # African Languages - COMMENT OUT until installed
    # 'amharic': 'amh',
    # 'afrikaans': 'afr',
    # 'swahili': 'swa',
    # 'yoruba': 'yor',
    # 'hausa': 'hau',
    # 'igbo': 'ibo',
    # 'somali': 'som',
    # 'zulu': 'zul',
    # 'xhosa': 'xho',
    
    # Indian Languages
    # 'hindi': 'hin',
    # 'bengali': 'ben',
    # 'tamil': 'tam',
    # 'telugu': 'tel',
    # 'marathi': 'mar',
    # 'urdu': 'urd',
    # 'gujarati': 'guj',
    # 'punjabi': 'pan'
}

# Update LANGUAGE_GROUPS to only include installed languages
LANGUAGE_GROUPS = {
    'european': [lang for lang in ['english', 'spanish', 'french', 'german', 'italian', 'portuguese'] if lang in SUPPORTED_LANGUAGES],
    # 'asian': [lang for lang in ['chinese_simplified', 'japanese', 'korean', 'thai', 'vietnamese'] if lang in SUPPORTED_LANGUAGES],
    # 'middle_eastern': [lang for lang in ['arabic', 'hebrew', 'turkish', 'persian'] if lang in SUPPORTED_LANGUAGES],
    # 'african': [lang for lang in ['amharic', 'afrikaans', 'swahili', 'yoruba', 'hausa', 'igbo', 'somali', 'zulu', 'xhosa'] if lang in SUPPORTED_LANGUAGES],
    # 'indian': [lang for lang in ['hindi', 'bengali', 'tamil', 'telugu', 'marathi', 'urdu', 'gujarati', 'punjabi'] if lang in SUPPORTED_LANGUAGES],
    'other': []
}

# Remove empty groups
LANGUAGE_GROUPS = {k: v for k, v in LANGUAGE_GROUPS.items() if v}

# Language display names for the menu (only for installed languages)
LANGUAGE_DISPLAY_NAMES = {
    'english': 'English 🇺🇸',
    'spanish': 'Spanish 🇪🇸', 
    'french': 'French 🇫🇷',
    'german': 'German 🇩🇪',
    'italian': 'Italian 🇮🇹',
    'portuguese': 'Portuguese 🇵🇹',
    # 'russian': 'Russian 🇷🇺',
    # 'dutch': 'Dutch 🇳🇱',
    # 'swedish': 'Swedish 🇸🇪',
    # 'polish': 'Polish 🇵🇱',
    # 'ukrainian': 'Ukrainian 🇺🇦',
    # 'greek': 'Greek 🇬🇷',
    # 'chinese_simplified': 'Chinese Simplified 🇨🇳',
    # 'japanese': 'Japanese 🇯🇵',
    # 'korean': 'Korean 🇰🇷',
    # 'thai': 'Thai 🇹🇭',
    # 'vietnamese': 'Vietnamese 🇻🇳',
    # 'arabic': 'Arabic 🇸🇦',
    # 'hebrew': 'Hebrew 🇮🇱',
    # 'turkish': 'Turkish 🇹🇷',
    # 'persian': 'Persian 🇮🇷',
    # 'amharic': 'Amharic 🇪🇹',
    # 'afrikaans': 'Afrikaans 🇿🇦',
    # 'swahili': 'Swahili 🇰🇪',
    # 'yoruba': 'Yoruba 🇳🇬',
    # 'hausa': 'Hausa 🇳🇬',
    # 'igbo': 'Igbo 🇳🇬',
    # 'somali': 'Somali 🇸🇴',
    # 'zulu': 'Zulu 🇿🇦',
    # 'xhosa': 'Xhosa 🇿🇦',
    # 'hindi': 'Hindi 🇮🇳',
    # 'bengali': 'Bengali 🇧🇩',
    # 'tamil': 'Tamil 🇮🇳',
    # 'telugu': 'Telugu 🇮🇳',
    # 'marathi': 'Marathi 🇮🇳',
    # 'urdu': 'Urdu 🇵🇰',
    # 'gujarati': 'Gujarati 🇮🇳',
    # 'punjabi': 'Punjabi 🇮🇳'
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