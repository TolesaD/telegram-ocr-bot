import os
import logging
import asyncio
import signal
import sys
import subprocess
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
    'CHANNEL': '@ImageToTextConverter',
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

# Import OCR components
try:
    from utils.smart_ocr import smart_ocr_processor
    OCR_AVAILABLE = True
    logger.info("✅ Smart OCR components imported successfully")
except ImportError as e:
    logger.error(f"Smart OCR import failed: {e}")
    OCR_AVAILABLE = False
    # Fallback to basic OCR
    try:
        from utils.image_processing import ocr_processor
        logger.info("✅ Using basic OCR as fallback")
    except ImportError:
        logger.error("All OCR imports failed")
        OCR_AVAILABLE = False

# IMPORTANT: Enhanced TextFormatter
try:
    from utils.text_formatter import TextFormatter
    TEXT_FORMATTER_AVAILABLE = True
    logger.info("✅ Text formatter imported successfully")
except ImportError as e:
    logger.error(f"Text formatter import failed: {e}")
    TEXT_FORMATTER_AVAILABLE = False
    # Create enhanced fallback
    class EnhancedTextFormatter:
        @staticmethod
        def format_text(text, format_type='plain'):
            """Enhanced text formatting with proper HTML support"""
            if not text:
                return text
                
            if format_type == 'html':
                # Proper HTML formatting with preserved spacing
                formatted = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Preserve multiple spaces and newlines
                formatted = formatted.replace('  ', ' &nbsp;').replace('\n', '<br>')
                return f"<pre>{formatted}</pre>"
            else:
                # Plain text - return as is
                return text
    TextFormatter = EnhancedTextFormatter
    logger.info("✅ Using enhanced text formatter fallback")

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

def get_channel_keyboard():
    """Get channel join keyboard"""
    from handlers.start import get_channel_keyboard as start_channel_keyboard
    return start_channel_keyboard()

# ===== ENHANCED HANDLER FUNCTIONS =====

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - imported from handlers.start"""
    try:
        from handlers.start import start_command as start_handler
        await start_handler(update, context)
    except ImportError as e:
        logger.error(f"Start handler import failed: {e}")
        await update.message.reply_text(
            "👋 Welcome! Send me an image to extract text.",
            parse_mode='Markdown',
            reply_markup=get_reply_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
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
    """Settings command"""
    user_id = update.effective_user.id
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
    """Statistics command"""
    user_id = update.effective_user.id
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
    """Convert command"""
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

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ENHANCED image handler with improved OCR and persistent channel checking"""
    message = update.message
    
    try:
        # Apply channel membership check for ALL image handlers
        from handlers.start import check_channel_membership
        user_id = update.effective_user.id
        has_joined = await check_channel_membership(update, context, user_id, force_check=True)
        
        if not has_joined:
            from handlers.start import show_channel_requirement
            await show_channel_requirement(update, context)
            return

        if not message.photo:
            await message.reply_text("Please send an image containing text.")
            return

        # Send initial message
        processing_msg = await message.reply_text("🔄 Processing your image with enhanced OCR...")
        
        # Download image with timeout
        try:
            photo = message.photo[-1]
            photo_file = await photo.get_file()
            photo_bytes = await asyncio.wait_for(
                photo_file.download_as_bytearray(),
                timeout=15.0
            )
            logger.info(f"✅ Downloaded image: {len(photo_bytes)} bytes")
        except asyncio.TimeoutError:
            await processing_msg.edit_text("❌ Image download timed out. Please try again.")
            return
        except Exception as e:
            logger.error(f"Download error: {e}")
            await processing_msg.edit_text("❌ Failed to download image. Please try again.")
            return
        
        # Process with ENHANCED OCR
        await processing_msg.edit_text("🔍 Analyzing image with enhanced text detection...")
        
        if not OCR_AVAILABLE:
            await processing_msg.edit_text("❌ OCR service is currently unavailable. Please try again later.")
            return
        
        try:
            # Try enhanced OCR first for blurry images
            try:
                from utils.enhanced_ocr import enhanced_ocr_processor
                extracted_text = await asyncio.wait_for(
                    enhanced_ocr_processor.extract_text_enhanced(bytes(photo_bytes)),
                    timeout=60.0  # Increased timeout for enhanced processing
                )
            except ImportError:
                # Fallback to smart OCR
                extracted_text = await asyncio.wait_for(
                    smart_ocr_processor.extract_text_smart(bytes(photo_bytes)),
                    timeout=45.0
                )
            
            logger.info(f"📝 OCR completed, extracted {len(extracted_text) if extracted_text else 0} characters")
            
        except asyncio.TimeoutError:
            await processing_msg.edit_text("❌ OCR processing took too long. Please try with a smaller or clearer image.")
            return
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            await processing_msg.edit_text("❌ Error during text extraction. Please try again with a different image.")
            return
        
        # Handle OCR result - IMPROVED VALIDATION
        if not extracted_text or any(msg in extracted_text for msg in [
            "No readable text", "Processing took", "Error processing", "Unable to process"
        ]):
            await processing_msg.edit_text("❌ No text could be extracted from the image. Please ensure the image contains clear, readable text.")
            return
        
        # Enhanced text validation
        clean_text = extracted_text.strip()
        if len(clean_text) < 3:  # Reduced threshold for blurry images
            await processing_msg.edit_text("❌ Extracted text is too short or unclear. Please try with a clearer image containing more text.")
            return
        
        # Format and send result
        user_id = update.effective_user.id
        try:
            user = db.get_user(user_id)
            text_format = user.get('settings', {}).get('text_format', 'plain') if user else 'plain'
        except:
            text_format = 'plain'
        
        # Format the text using enhanced formatter
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # Truncate if too long for Telegram
        if len(formatted_text) > 4000:
            formatted_text = formatted_text[:3900] + "\n\n... [text truncated due to length]"
        
        # Send result - CLEAN OUTPUT
        try:
            if text_format == 'html':
                await processing_msg.edit_text(
                    formatted_text,
                    parse_mode='HTML'
                )
            else:
                await processing_msg.edit_text(
                    formatted_text,
                    parse_mode=None  # Plain text, no formatting
                )
            
            # Log success
            try:
                db.log_ocr_request({
                    'user_id': user_id,
                    'format': text_format,
                    'text_length': len(extracted_text),
                    'processing_time': 0,
                    'status': 'success'
                })
            except Exception as e:
                logger.error(f"Logging error: {e}")
                
        except Exception as e:
            logger.error(f"Message sending error: {e}")
            # Fallback: send as plain text
            await processing_msg.edit_text(extracted_text[:3000])
            
    except asyncio.TimeoutError:
        logger.error("Overall image processing timeout")
        try:
            await message.reply_text("❌ Processing timed out. Please try with a smaller or clearer image.")
        except:
            pass
    except Exception as e:
        logger.error(f"Unexpected error in handle_image: {e}")
        try:
            await message.reply_text("❌ An unexpected error occurred. Please try again with a different image.")
        except:
            pass

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback received: {data}")
    
    # Handle channel membership check first
    if data == "check_membership":
        try:
            from handlers.start import handle_membership_check
            await handle_membership_check(update, context)
            return
        except ImportError as e:
            logger.error(f"Membership handler import failed: {e}")
            await query.answer("✅ Welcome! You're all set.")
            await show_main_menu(query)
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
    """Main function"""
    try:
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found")
            return

        # Create application with post_init
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .build()
        )
        
        # Store database
        application.bot_data['db'] = db
        
        # Add handlers
        handlers = [
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("settings", settings_command),
            CommandHandler("stats", stats_command),
            CommandHandler("convert", convert_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message),
            MessageHandler(filters.PHOTO, handle_image),
            CallbackQueryHandler(handle_callback),
        ]
        
        for handler in handlers:
            application.add_handler(handler)
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered")
        logger.info("🚀 Starting bot...")
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()