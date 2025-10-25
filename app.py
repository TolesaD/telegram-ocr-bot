import os
import logging
import asyncio
import signal
import sys
import subprocess
import time
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Signal handlers
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Load environment
load_dotenv()

# Fallback values
FALLBACK_VALUES = {
    'BOT_TOKEN': '8327516444:AAGblijJShx3Uh9cWU7coADtUl_PnAeDZ5A',
    'SUPPORT_BOT': '@ImageToTextConverterSupportBot',
    'CHANNEL_USERNAME': 'ImageToTextConverter',
    'ADMIN_IDS': '417079598'
}

for key, fallback_value in FALLBACK_VALUES.items():
    if not os.getenv(key):
        os.environ[key] = fallback_value
        logger.warning(f"Using fallback for {key}")

# Import language support if available
try:
    from ocr_engine.language_support import detect_primary_language, get_language_name
    LANGUAGE_SUPPORT_AVAILABLE = True
    logger.info("✅ Language support module imported")
except ImportError as e:
    LANGUAGE_SUPPORT_AVAILABLE = False
    logger.warning(f"❌ Language support module not available: {e}")

# Import database - POSTGRESQL ONLY VERSION
try:
    from database.postgres_db import PostgresDatabase
    db = PostgresDatabase()
    logger.info("✅ PostgreSQL database imported successfully")
except Exception as e:
    logger.error(f"PostgreSQL database import failed: {e}")
    # Fallback to mock database
    class MockDB:
        def __init__(self): 
            self.is_mock = True
            self.users_data = {}
            self.requests_data = []
        
        def get_user(self, user_id): 
            return self.users_data.get(user_id)
        
        def insert_user(self, user_data): 
            self.users_data[user_data['user_id']] = user_data
            return True
        
        def update_user_settings(self, user_id, settings): 
            if user_id in self.users_data:
                if 'settings' not in self.users_data[user_id]:
                    self.users_data[user_id]['settings'] = {}
                self.users_data[user_id]['settings'].update(settings)
            return True
        
        def log_ocr_request(self, request_data): 
            self.requests_data.append(request_data)
            return True
        
        def get_user_stats(self, user_id): 
            user_requests = [r for r in self.requests_data if r.get('user_id') == user_id]
            return {
                'total_requests': len(user_requests),
                'recent_requests': user_requests[-10:][::-1],
                'success_rate': 100,
                'success_count': len(user_requests)
            }
    
    db = MockDB()
    logger.info("Using mock database as fallback")

# Import OCR with better error handling
ocr_processor = None
performance_monitor = None
TextFormatter = None

try:
    from utils.image_processing import ocr_processor, performance_monitor
    from utils.text_formatter import TextFormatter
    logger.info("✅ OCR components imported successfully")
except ImportError as e:
    logger.error(f"OCR import failed: {e}")
    # Create fallback OCR processor
    class FallbackOCRProcessor:
        async def extract_text_optimized(self, image_bytes, language=None):
            return "❌ OCR system is currently unavailable. Please try again later."
    
    class FallbackPerformanceMonitor:
        def record_request(self, processing_time):
            pass
        def get_stats(self):
            return "System initializing"
    
    class FallbackTextFormatter:
        @staticmethod
        def format_text(text, format_type='plain'):
            return text if text else "No text available"
        @staticmethod
        def split_long_message(text, max_length=4000):
            return [text] if text else [""]
    
    ocr_processor = FallbackOCRProcessor()
    performance_monitor = FallbackPerformanceMonitor()
    TextFormatter = FallbackTextFormatter

# ===== CHANNEL VERIFICATION =====

async def check_channel_membership(user_id, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced channel membership check that works on every message"""
    try:
        CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'ImageToTextConverter')
        # Ensure channel username has @ prefix
        channel_username = f"@{CHANNEL_USERNAME}" if not CHANNEL_USERNAME.startswith('@') else CHANNEL_USERNAME
        
        logger.info(f"🔍 Checking channel membership for user {user_id} in {channel_username}")
        
        # Check if user is member of channel
        chat_member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        
        # User must be member, administrator, or creator
        is_member = chat_member.status in ['member', 'administrator', 'creator']
        logger.info(f"📊 User {user_id} membership status: {chat_member.status} -> {'Member' if is_member else 'Not Member'}")
        
        return is_member
    except Exception as e:
        logger.error(f"Channel membership check failed: {e}")
        # Allow access if check fails to avoid blocking legitimate users
        return True

def get_channel_keyboard():
    """Get channel join keyboard"""
    CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'ImageToTextConverter')
    channel_username = f"@{CHANNEL_USERNAME}" if not CHANNEL_USERNAME.startswith('@') else CHANNEL_USERNAME
    
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== KEYBOARD LAYOUTS =====

def get_main_keyboard():
    """Get the main inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("📸 Convert Image", callback_data="convert_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reply_keyboard():
    """Get persistent reply keyboard (square buttons at bottom)"""
    keyboard = [
        ["📸 Convert Image", "⚙️ Settings"],
        ["📊 Statistics", "❓ Help"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_settings_keyboard():
    """Get settings keyboard"""
    keyboard = [
        [InlineKeyboardButton("📄 Plain Text", callback_data="set_format_plain")],
        [InlineKeyboardButton("🌐 HTML Format", callback_data="set_format_html")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Simple back to main keyboard"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

# ===== HANDLER FUNCTIONS =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with enhanced channel verification"""
    user_id = update.effective_user.id
    logger.info(f"🚀 Start command received from user {user_id}")
    
    # Check channel membership
    is_member = await check_channel_membership(user_id, context)
    
    if not is_member:
        logger.info(f"❌ User {user_id} not in channel, requesting join")
        await update.message.reply_text(
            "👋 Welcome to Image to Text Converter!\n\n"
            "📢 To use this bot, please join our channel first:\n\n"
            "🔹 Get updates on new features\n"
            "🔹 Learn about improvements\n"
            "🔹 Stay informed about the bot\n\n"
            "Join the channel below and then click **'I've Joined'** to continue:",
            parse_mode='Markdown',
            reply_markup=get_channel_keyboard()
        )
        return
    
    # User is member, show main menu
    logger.info(f"✅ User {user_id} is channel member, showing main menu")
    await update.message.reply_text(
        "👋 *Welcome to Image to Text Converter!*\n\n"
        "I can extract text from images in *70+ languages*! 🌍\n\n"
        "✨ *How to use:*\n"
        "1. Send me an image with text\n"
        "2. I'll automatically detect the language\n"
        "3. Get your extracted text instantly\n\n"
        "💡 *Tips for best results:*\n"
        "• Clear, well-lit images\n"
        "• Horizontal text alignment\n"
        "• Good contrast between text and background\n\n"
        "Choose an option below to get started:",
        parse_mode='Markdown',
        reply_markup=get_reply_keyboard()
    )
    
    # Initialize user in database
    try:
        user = db.get_user(user_id)
        if not user:
            user_data = {
                'user_id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'last_name': update.effective_user.last_name,
                'settings': {'text_format': 'plain'}
            }
            db.insert_user(user_data)
            logger.info(f"✅ New user {user_id} added to database")
    except Exception as e:
        logger.error(f"Error initializing user {user_id}: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with channel verification"""
    user_id = update.effective_user.id
    
    # Check channel membership
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "📢 Please join our channel to access help!\n\n"
            "Join the channel below and then send /start again.",
            reply_markup=get_channel_keyboard()
        )
        return
    
    await update.message.reply_text(
        "❓ *Help Guide*\n\n"
        "**How to use:**\n"
        "1. Send an image with text\n"
        "2. Get extracted text automatically\n\n"
        "**Available Commands:**\n"
        "/start - Start the bot\n" 
        "/help - Show this help\n"
        "/settings - Change text format\n"
        "/stats - View your statistics\n"
        "/convert - Convert an image\n\n"
        "**Tips for best results:**\n"
        "• Use clear, well-lit images\n"
        "• Ensure text is readable\n"
        "• Horizontal text works best\n"
        "• High contrast improves accuracy\n\n"
        "🌍 **70+ languages supported automatically!**",
        parse_mode='Markdown',
        reply_markup=get_reply_keyboard()
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command with channel verification"""
    user_id = update.effective_user.id
    
    # Check channel membership
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "📢 Please join our channel to access settings!\n\n"
            "Join the channel below and then send /start again.",
            reply_markup=get_channel_keyboard()
        )
        return
    
    try:
        user = db.get_user(user_id)
        current_format = user.get('settings', {}).get('text_format', 'plain') if user else 'plain'
    except:
        current_format = 'plain'
    
    await update.message.reply_text(
        f"⚙️ *Settings*\n\n"
        f"Current format: **{current_format.upper()}**\n\n"
        f"Choose your preferred text format:",
        parse_mode='Markdown',
        reply_markup=get_settings_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Statistics command with channel verification"""
    user_id = update.effective_user.id
    
    # Check channel membership
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "📢 Please join our channel to view statistics!\n\n"
            "Join the channel below and then send /start again.",
            reply_markup=get_channel_keyboard()
        )
        return
    
    try:
        stats = db.get_user_stats(user_id)
        total = stats.get('total_requests', 0)
        success_rate = stats.get('success_rate', 0)
        recent_count = len(stats.get('recent_requests', []))
        
        await update.message.reply_text(
            f"📊 *Your Statistics*\n\n"
            f"• 📈 Total requests: **{total}**\n"
            f"• ✅ Success rate: **{success_rate:.1f}%**\n"
            f"• 🕒 Recent activity: **{recent_count}** requests\n"
            f"• 🌍 Languages: **70+ supported**\n\n"
            f"Keep converting images to build your stats! 📸",
            parse_mode='Markdown',
            reply_markup=get_reply_keyboard()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await update.message.reply_text(
            "📊 *Statistics*\n\nNo data yet. Start converting images to see your statistics!",
            parse_mode='Markdown',
            reply_markup=get_reply_keyboard()
        )

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert command with channel verification"""
    user_id = update.effective_user.id
    
    # Check channel membership
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        await update.message.reply_text(
            "📢 Please join our channel to convert images!\n\n"
            "Join the channel below and then send /start again.",
            reply_markup=get_channel_keyboard()
        )
        return
    
    await update.message.reply_text(
        "📸 *Ready to convert!*\n\n"
        "Send me an image containing text and I'll extract it for you.\n\n"
        "💡 **Tips for best results:**\n"
        "• Clear, focused images\n"
        "• Good lighting\n" 
        "• Horizontal text\n"
        "• High contrast\n\n"
        "🌍 **Automatic language detection**\n"
        "Supports 70+ languages including English, Amharic, Spanish, French, Arabic, and many more!",
        parse_mode='Markdown',
        reply_markup=get_reply_keyboard()
    )

async def handle_message_with_channel_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced message handler with channel verification"""
    user_id = update.effective_user.id
    
    # Check channel membership for all messages except start command
    if update.message and update.message.text and not update.message.text.startswith('/start'):
        is_member = await check_channel_membership(user_id, context)
        if not is_member:
            logger.info(f"❌ User {user_id} not in channel, blocking message: {update.message.text}")
            await update.message.reply_text(
                "📢 Please join our channel to continue using the bot!\n\n"
                "Join the channel below and then send /start again.",
                reply_markup=get_channel_keyboard()
            )
            return
    
    # Proceed with normal message handling
    await handle_text_message(update, context)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from reply keyboard"""
    text = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Text message received: {text} from user {user_id}")
    
    if text == "📸 Convert Image":
        await update.message.reply_text(
            "📸 *Ready to convert!*\n\n"
            "Send me an image containing text and I'll extract it for you.\n\n"
            "💡 **Tips for best results:**\n"
            "• Clear, focused images\n"
            "• Good lighting\n" 
            "• Horizontal text\n"
            "• High contrast\n\n"
            "🌍 **Automatic language detection**\n"
            "Supports 70+ languages!",
            parse_mode='Markdown',
            reply_markup=get_reply_keyboard()
        )
    
    elif text == "⚙️ Settings":
        user = db.get_user(user_id)
        current_format = user.get('settings', {}).get('text_format', 'plain') if user else 'plain'
        
        await update.message.reply_text(
            f"⚙️ *Settings*\n\n"
            f"Current format: **{current_format.upper()}**\n\n"
            f"Choose your preferred text format:",
            parse_mode='Markdown',
            reply_markup=get_settings_keyboard()
        )
    
    elif text == "📊 Statistics":
        try:
            stats = db.get_user_stats(user_id)
            total = stats.get('total_requests', 0)
            success_rate = stats.get('success_rate', 0)
            recent_count = len(stats.get('recent_requests', []))
            
            await update.message.reply_text(
                f"📊 *Your Statistics*\n\n"
                f"• 📈 Total requests: **{total}**\n"
                f"• ✅ Success rate: **{success_rate:.1f}%**\n"
                f"• 🕒 Recent activity: **{recent_count}** requests\n"
                f"• 🌍 Languages: **70+ supported**\n\n"
                f"Keep converting images to build your stats! 📸",
                parse_mode='Markdown',
                reply_markup=get_reply_keyboard()
            )
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await update.message.reply_text(
                "📊 *Statistics*\n\nNo data yet. Start converting images to see your statistics!",
                parse_mode='Markdown',
                reply_markup=get_reply_keyboard()
            )
    
    elif text == "❓ Help":
        await update.message.reply_text(
            "❓ *Help Guide*\n\n"
            "**How to use:**\n"
            "1. Send an image with text\n"
            "2. Get extracted text automatically\n\n"
            "**Available Options:**\n"
            "• 📸 Convert Image - Extract text from images\n"
            "• ⚙️ Settings - Change text format\n"
            "• 📊 Statistics - View your usage\n"
            "• ❓ Help - Get instructions\n\n"
            "💡 **Tips for best results:**\n"
            "• Clear, well-lit images\n"
            "• Readable, focused text\n"
            "• Horizontal alignment\n"
            "• High contrast\n\n"
            "🌍 **70+ languages supported automatically!**",
            parse_mode='Markdown',
            reply_markup=get_reply_keyboard()
        )
    
    else:
        # Handle unknown text
        await update.message.reply_text(
            "🤖 *Main Menu*\n\n"
            "Choose an option below:\n\n"
            "📸 **Convert Image** - Extract text from images\n"
            "⚙️ **Settings** - Change text format\n"
            "📊 **Statistics** - View your usage stats\n"
            "❓ **Help** - Get help and instructions",
            parse_mode='Markdown',
            reply_markup=get_reply_keyboard()
        )

async def handle_image_with_channel_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced image handler with channel verification"""
    user_id = update.effective_user.id
    
    # Check channel membership for image processing
    is_member = await check_channel_membership(user_id, context)
    if not is_member:
        logger.info(f"❌ User {user_id} not in channel, blocking image processing")
        await update.message.reply_text(
            "📢 Please join our channel to use the OCR feature!\n\n"
            "Join the channel below and then send /start again.",
            reply_markup=get_channel_keyboard()
        )
        return
    
    # Proceed with normal image processing
    await handle_image(update, context)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages"""
    try:
        message = update.message
        if not message.photo:
            await message.reply_text("Please send an image containing text.")
            return

        processing_msg = await message.reply_text("🔄 Processing your image...")
        
        # Download image
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Extract text
        extracted_text = await ocr_processor.extract_text_optimized(bytes(photo_bytes))
        
        if not extracted_text or "No readable text" in extracted_text:
            await processing_msg.edit_text(
                "❌ No readable text found.\n\nTry with a clearer image with better lighting."
            )
            return
        
        # Get user format preference
        user_id = update.effective_user.id
        try:
            user = db.get_user(user_id)
            text_format = user.get('settings', {}).get('text_format', 'plain') if user else 'plain'
        except:
            text_format = 'plain'
        
        # Format text
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # LANGUAGE DETECTION
        if LANGUAGE_SUPPORT_AVAILABLE:
            detected_lang = detect_primary_language(extracted_text)
            lang_name = get_language_name(detected_lang)
            language_info = f" (Detected: {lang_name})"
        else:
            language_info = ""
        
        # Send result with language info
        if text_format == 'html':
            await processing_msg.edit_text(
                f"✅ **Text Extracted**{language_info} (HTML Format)\n\n{formatted_text}",
                parse_mode='HTML'
            )
        else:
            await processing_msg.edit_text(
                f"✅ **Text Extracted**{language_info}\n\n{formatted_text}",
                parse_mode='Markdown'
            )
        
        # Log request
        try:
            db.log_ocr_request({
                'user_id': user_id,
                'format': text_format,
                'text_length': len(extracted_text),
                'processing_time': 0,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error logging request: {e}")
            
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        try:
            await update.message.reply_text("❌ Error processing image. Please try again with a different image.")
        except:
            pass

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    logger.info(f"Callback received: {data} from user {user_id}")
    
    # Handle channel membership check
    if data == "check_membership":
        is_member = await check_channel_membership(user_id, context)
        if is_member:
            await query.answer("✅ Thank you for joining! Welcome!")
            await show_main_menu(query)
        else:
            await query.answer("❌ Please join the channel first!", show_alert=True)
            await query.edit_message_text(
                "❌ *Channel Membership Required*\n\n"
                "I still don't see you in our channel. Please:\n\n"
                "1. Click the 'Join Channel' button below\n"
                "2. Actually join the channel (don't just open it)\n"
                "3. Come back and click 'I've Joined' again\n\n"
                "This helps us keep the bot running and improved! 🚀",
                parse_mode='Markdown',
                reply_markup=get_channel_keyboard()
            )
        return
    
    # Check channel membership for other callbacks (except main_menu)
    if data != "main_menu":
        is_member = await check_channel_membership(user_id, context)
        if not is_member:
            await query.answer("❌ Please join the channel first!", show_alert=True)
            await query.edit_message_text(
                "📢 *Channel Membership Required*\n\n"
                "To use this feature, please join our channel first.\n\n"
                "Join the channel below and then click 'I've Joined':",
                parse_mode='Markdown',
                reply_markup=get_channel_keyboard()
            )
            return
    
    # Handle other callbacks
    if data == "main_menu":
        await show_main_menu(query)
    
    elif data == "convert_image":
        await show_convert_menu(query)
    
    elif data == "settings":
        await show_settings_menu(query)
    
    elif data == "statistics":
        await show_statistics_menu(query)
    
    elif data == "help":
        await show_help_menu(query)
    
    elif data.startswith("set_format_"):
        await handle_format_change(query, data)
    
    else:
        await query.edit_message_text("❌ Unknown command. Returning to main menu.")
        await show_main_menu(query)

# ===== MENU FUNCTIONS FOR CALLBACKS =====

async def show_main_menu(query):
    """Show main menu for callback"""
    await query.edit_message_text(
        "🤖 *Main Menu*\n\n"
        "Choose an option below:\n\n"
        "📸 **Convert Image** - Extract text from images\n"
        "⚙️ **Settings** - Change text format\n"
        "📊 **Statistics** - View your usage stats\n"
        "❓ **Help** - Get help and instructions",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def show_convert_menu(query):
    """Show convert menu for callback"""
    await query.edit_message_text(
        "📸 *Convert Image*\n\n"
        "Ready to extract text from your images!\n\n"
        "✨ **Simply send me:**\n"
        "• Any image containing text\n"
        "• Photos of documents\n"
        "• Screenshots with text\n"
        "• Signs, menus, or books\n\n"
        "🌍 **70+ languages supported automatically!**\n\n"
        "💡 **Tips for best results:**\n"
        "• Clear, well-lit images\n"
        "• Focused, readable text\n"
        "• High contrast\n"
        "• Horizontal text alignment",
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

async def show_settings_menu(query):
    """Show settings menu for callback"""
    user_id = query.from_user.id
    try:
        user = db.get_user(user_id)
        current_format = user.get('settings', {}).get('text_format', 'plain') if user else 'plain'
    except:
        current_format = 'plain'
    
    await query.edit_message_text(
        f"⚙️ *Settings*\n\n"
        f"Current format: **{current_format.upper()}**\n\n"
        f"Choose your preferred text format:",
        parse_mode='Markdown',
        reply_markup=get_settings_keyboard()
    )

async def show_statistics_menu(query):
    """Show statistics menu for callback"""
    user_id = query.from_user.id
    try:
        stats = db.get_user_stats(user_id)
        total = stats.get('total_requests', 0)
        success_rate = stats.get('success_rate', 0)
        recent_count = len(stats.get('recent_requests', []))
        
        await query.edit_message_text(
            f"📊 *Your Statistics*\n\n"
            f"• 📈 Total requests: **{total}**\n"
            f"• ✅ Success rate: **{success_rate:.1f}%**\n"
            f"• 🕒 Recent activity: **{recent_count}** requests\n"
            f"• 🌍 Languages: **70+ supported**\n\n"
            f"Keep converting images to build your stats! 📸",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        await query.edit_message_text(
            "📊 *Statistics*\n\nNo data yet. Start converting images to see your statistics!",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )

async def show_help_menu(query):
    """Show help menu for callback"""
    await query.edit_message_text(
        "❓ *Help Center*\n\n"
        "**How to use:**\n"
        "1. Send an image with text\n"
        "2. Get extracted text automatically\n\n"
        "**Available Options:**\n"
        "• Convert Image - Extract text from images\n"
        "• Settings - Change text format\n"
        "• Statistics - View your usage\n"
        "• Help - Get instructions\n\n"
        "💡 **Tips for best results:**\n"
        "• Clear, well-lit images\n"
        "• Readable, focused text\n"
        "• Horizontal alignment\n"
        "• High contrast\n\n"
        "🌍 **70+ languages supported automatically!**",
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

async def handle_format_change(query, data):
    """Handle format change for callback"""
    text_format = data.replace("set_format_", "")
    user_id = query.from_user.id
    
    try:
        # Update user settings
        user = db.get_user(user_id)
        if user:
            settings = user.get('settings', {})
            settings['text_format'] = text_format
            db.update_user_settings(user_id, settings)
        else:
            user_data = {
                'user_id': user_id,
                'settings': {'text_format': text_format}
            }
            db.insert_user(user_data)
        
        format_name = "Plain Text" if text_format == 'plain' else "HTML Format"
        await query.edit_message_text(
            f"✅ Format set to **{format_name}**\n\n"
            f"Your future text extractions will use this format.",
            parse_mode='Markdown',
            reply_markup=get_back_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Format change error: {e}")
        await query.edit_message_text(
            "❌ Error saving settings. Please try again.",
            reply_markup=get_back_keyboard()
        )

async def set_bot_commands(application):
    """Set bot commands for menu"""
    try:
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help guide"),
            BotCommand("settings", "Change text format"),
            BotCommand("stats", "View your statistics"),
            BotCommand("convert", "Convert an image"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands set successfully")
    except Exception as e:
        logger.error(f"Error setting bot commands: {e}")

async def post_init(application):
    """Run after bot starts"""
    await set_bot_commands(application)
    logger.info("🚀 Bot is ready and commands are set!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Error handler"""
    logger.error(f"Error: {context.error}")
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ An error occurred. Please try again."
            )
    except:
        pass

def main():
    """Main function with better error handling"""
    try:
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found")
            return

        logger.info("🔄 Initializing bot application...")
        
        # Create application with timeout handling
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .build()
        )
        
        # Store database
        application.bot_data['db'] = db
        
        # Add handlers with enhanced channel verification
        handlers = [
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("settings", settings_command),
            CommandHandler("stats", stats_command),
            CommandHandler("convert", convert_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_with_channel_check),
            MessageHandler(filters.PHOTO, handle_image_with_channel_check),
            CallbackQueryHandler(handle_callback),
        ]
        
        for handler in handlers:
            application.add_handler(handler)
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered with enhanced channel verification")
        logger.info("🚀 Starting bot polling...")
        
        # Start polling with better error handling
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        logger.info("🔄 Attempting to restart in 5 seconds...")
        time.sleep(5)
        main()  # Recursive restart

if __name__ == "__main__":
    main()