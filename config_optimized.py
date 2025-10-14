"""
🎯 Production Configuration - ImageToText Pro Bot
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==================== BOT CONFIGURATION ====================
BOT_NAME = "ImageToText Pro"
VERSION = "2.0.0"
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ==================== DATABASE CONFIGURATION ====================
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = "image_to_text_pro"

# ==================== OCR ENGINE CONFIGURATION ====================
OCR_ENGINES = {
    'tesseract': {
        'enabled': True,
        'priority': 1,
        'timeout': 10
    }
}

# ==================== LANGUAGE SUPPORT ====================
SUPPORTED_LANGUAGES = {
    # European Languages
    'english': {'code': 'eng', 'flag': '🇺🇸', 'name': 'English'},
    'spanish': {'code': 'spa', 'flag': '🇪🇸', 'name': 'Spanish'},
    'french': {'code': 'fra', 'flag': '🇫🇷', 'name': 'French'},
    'german': {'code': 'deu', 'flag': '🇩🇪', 'name': 'German'},
    'italian': {'code': 'ita', 'flag': '🇮🇹', 'name': 'Italian'},
    'portuguese': {'code': 'por', 'flag': '🇵🇹', 'name': 'Portuguese'},
    'russian': {'code': 'rus', 'flag': '🇷🇺', 'name': 'Russian'},
    
    # Asian Languages
    'chinese_simplified': {'code': 'chi_sim', 'flag': '🇨🇳', 'name': 'Chinese Simplified'},
    'japanese': {'code': 'jpn', 'flag': '🇯🇵', 'name': 'Japanese'},
    'korean': {'code': 'kor', 'flag': '🇰🇷', 'name': 'Korean'},
    
    # Middle Eastern Languages
    'arabic': {'code': 'ara', 'flag': '🇸🇦', 'name': 'Arabic'},
    'hindi': {'code': 'hin', 'flag': '🇮🇳', 'name': 'Hindi'},
    'turkish': {'code': 'tur', 'flag': '🇹🇷', 'name': 'Turkish'},
    
    # Additional European
    'dutch': {'code': 'nld', 'flag': '🇳🇱', 'name': 'Dutch'},
    'swedish': {'code': 'swe', 'flag': '🇸🇪', 'name': 'Swedish'},
    'polish': {'code': 'pol', 'flag': '🇵🇱', 'name': 'Polish'},
    'ukrainian': {'code': 'ukr', 'flag': '🇺🇦', 'name': 'Ukrainian'},
    'greek': {'code': 'ell', 'flag': '🇬🇷', 'name': 'Greek'},
}

# Language display names for the menu
LANGUAGE_DISPLAY_NAMES = {
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
    'chinese_simplified': 'Chinese Simplified 🇨🇳',
    'japanese': 'Japanese 🇯🇵',
    'korean': 'Korean 🇰🇷',
    'arabic': 'Arabic 🇸🇦',
    'hindi': 'Hindi 🇮🇳',
    'turkish': 'Turkish 🇹🇷',
}

# Language groups for organized menu
LANGUAGE_GROUPS = {
    'popular': ['english', 'spanish', 'french', 'german', 'italian'],
    'european': ['portuguese', 'russian', 'dutch', 'swedish', 'polish', 'ukrainian', 'greek'],
    'asian': ['chinese_simplified', 'japanese', 'korean'],
    'middle_eastern': ['arabic', 'hindi', 'turkish']
}

# ==================== PERFORMANCE CONFIGURATION ====================
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
PROCESSING_TIMEOUT = 15  # seconds
MAX_CONCURRENT_PROCESSING = 5
CACHE_DURATION = 300  # 5 minutes

# ==================== TEXT FORMATTING ====================
FORMAT_OPTIONS = ['plain', 'markdown', 'html']

# ==================== CHANNEL CONFIGURATION ====================
ANNOUNCEMENT_CHANNEL = "@ImageToTextConverter"
CHANNEL_USERNAME = "ImageToTextConverter"

# ==================== SUPPORT CONFIGURATION ====================
SUPPORT_EMAIL = "tolesadebushe9@gmail.com"
SUPPORT_TEXT = f"""
📞 **Support & Contact**

For technical support, feature requests, or bug reports:

📧 Email: {SUPPORT_EMAIL}

We typically respond within 24 hours.

**Common Issues:**
• Blurry images - Use clear, high-contrast photos
• Language detection - Ensure correct language selection
• Large files - Images should be under 10MB
"""

# ==================== ADMIN CONFIGURATION ====================
ADMIN_IDS = []
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip().isdigit()]

# ==================== MESSAGES & TEXTS ====================
WELCOME_MESSAGE = """
🎉 **Welcome to ImageToText Pro!** 🤖

**Transform images into editable text with precision:**

✨ **Key Features:**
• 🚀 Multi-language OCR support
• 📝 Multiple text formats
• ⚡ Fast processing
• 💾 Save your preferences
• 🔍 High accuracy

**How to use:**
1. Send an image with text
2. Choose your preferred language
3. Get formatted text instantly

**Pro Tips:**
• Use clear, well-lit images
• Ensure text is focused
• Select the correct language
• High contrast works best

Ready to convert? Send an image now! 📸
"""

CHANNEL_REQUIREMENT_MESSAGE = """
📢 **Channel Membership Required**

To use ImageToText Pro, please join our official channel for:
• 🚀 Feature updates
• 💡 Usage tips  
• 🔧 Maintenance news
• 📢 Important announcements

**Quick Steps:**
1. Tap *Join Announcement Channel* below
2. Join the channel
3. Return and tap *I've Joined*
4. Start converting! 🎉

We keep announcements minimal and valuable! ✨
"""

# ==================== ERROR MESSAGES ====================
ERROR_MESSAGES = {
    'processing_timeout': "⏰ Processing took too long. Please try a smaller image or better lighting.",
    'no_text_found': "❌ No readable text found. Try a clearer image with better contrast.",
    'image_too_large': "📸 Image is too large. Please send images under 10MB.",
    'invalid_image': "🖼️ Invalid image format. Please send a valid image file.",
    'channel_required': "🔒 Channel membership required to use this bot.",
}