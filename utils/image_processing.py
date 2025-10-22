# app.py
import os
import logging
import asyncio
import signal
import sys
import subprocess
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update
from dotenv import load_dotenv

# Configure logging for Railway with enhanced OCR logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"📦 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Load environment variables
load_dotenv()

# Fallback values if environment variables are not set
FALLBACK_VALUES = {
    'BOT_TOKEN': '8327516444:AAGblijJShx3Uh9cWU7coADtUl_PnAeDZ5A',
    'MONGODB_URI': 'mongodb+srv://telegram-bot-user:KJMPN6R7SctEtlZZ@pythoncluster.dufidzj.mongodb.net/telegram_ocr_bot?retryWrites=true&w=majority',
    'SUPPORT_BOT': '@ImageToTextConverterSupportBot',
    'CHANNEL': '@ImageToTextConverter',
    'ADMIN_IDS': '417079598'
}

# Set fallback values if environment variables are missing
for key, fallback_value in FALLBACK_VALUES.items():
    if not os.getenv(key):
        os.environ[key] = fallback_value
        logger.warning(f"⚠️ Using fallback for {key}")

# Import database with enhanced error handling
try:
    from database.mongodb import db
    logger.info("✅ Database imported successfully")
except ImportError as e:
    logger.error(f"❌ Database import failed: {e}")
    # Create a simple mock database
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
                'recent_requests': user_requests[-5:][::-1]
            }
    
    db = MockDB()
    logger.info("✅ Using mock database")

# Enhanced OCR imports with better error handling
try:
    # Import OCR processor early to catch initialization errors
    from utils.image_processing import ocr_processor, performance_monitor
    logger.info("✅ OCR processor imported successfully")
    
    # Import text formatter
    from utils.text_formatter import TextFormatter
    logger.info("✅ Text formatter imported successfully")
    
except ImportError as e:
    logger.error(f"❌ OCR components import failed: {e}")
    raise

# Now import handlers with enhanced error handling
try:
    from handlers.start import handle_membership_check, force_check_membership, handle_start_callback
    from handlers.help import help_command, handle_help_callback
    from handlers.ocr import handle_image, handle_reformat, handle_ocr_callback
    from handlers.menu import (
        show_main_menu, show_settings_menu, show_statistics,
        handle_convert_image, show_format_menu,
        handle_format_change
    )
    
    # Import enhanced menu handlers
    from handlers.menu_enhanced import (
        show_enhanced_main_menu, 
        handle_quick_actions,
        show_quick_settings,
        show_quick_statistics,
        show_quick_help,
        get_main_menu_keyboard
    )
    
    logger.info("✅ All handlers imported successfully")
except ImportError as e:
    logger.error(f"❌ Handler import failed: {e}")
    # Create fallback handlers for critical functionality
    async def fallback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚀 Bot is starting... Please try again in a moment.")
    
    async def fallback_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("❓ Help system is initializing...")
    
    async def fallback_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📸 Image processing is temporarily unavailable. Please try again later.")
    
    # Assign fallback handlers
    help_command = fallback_help
    handle_image = fallback_image
    logger.warning("⚠️ Using fallback handlers due to import errors")

# Use enhanced main menu as start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with menu"""
    await show_enhanced_main_menu(update, context)

async def check_railway_environment():
    """Check if we're running on Railway and verify setup"""
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    if is_railway:
        logger.info("🚄 Running in Railway environment")
        
        # Verify Tesseract installation
        try:
            result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Tesseract found at: {result.stdout.strip()}")
            else:
                logger.error("❌ Tesseract not found in PATH on Railway")
                
            # Test Tesseract
            version_result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
            if version_result.returncode == 0:
                logger.info("✅ Tesseract is working on Railway")
                logger.info(f"📄 Tesseract output: {version_result.stdout.splitlines()[0]}")
            else:
                logger.error(f"❌ Tesseract test failed: {version_result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Railway Tesseract check failed: {e}")
    
    return is_railway

async def diagnose_tesseract_setup():
    """Diagnose Tesseract setup and available languages"""
    try:
        from utils.image_processing import ocr_processor
        import pytesseract
        
        logger.info("🔧 Running Tesseract diagnostics...")
        
        # Check Tesseract version
        version = pytesseract.get_tesseract_version()
        logger.info(f"✅ Tesseract version: {version}")
        
        # Check available languages
        logger.info(f"🌍 Available languages: {ocr_processor.available_languages}")
        
        # Check TESSDATA_PREFIX
        tessdata_prefix = os.getenv('TESSDATA_PREFIX', 'Not set')
        logger.info(f"📁 TESSDATA_PREFIX: {tessdata_prefix}")
        
        # Log language support status
        supported_langs = ['en', 'am', 'ar', 'zh', 'ja', 'ko', 'es', 'fr', 'de', 'ru']
        logger.info("🔤 Language Support Status:")
        for lang in supported_langs:
            status = "✅" if ocr_processor.is_language_available(lang) else "❌"
            tess_code = ocr_processor._get_tesseract_code_from_lang(lang)
            logger.info(f"   {status} {lang} - {tess_code}")
        
        # Log total available languages
        total_available = len(ocr_processor.available_languages)
        logger.info(f"📊 Total available languages: {total_available}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Tesseract diagnostics failed: {e}")
        return False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced error handling with better logging"""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Log the full traceback for debugging
    logger.error(f"Full error: {context.error}", exc_info=context.error)
    
    # Send user-friendly error message
    try:
        if update and update.effective_chat:
            error_msg = (
                "❌ An unexpected error occurred.\n\n"
                "🔧 **Quick Fixes:**\n"
                "• Try sending the image again\n"
                "• Ensure the image is clear and focused\n"
                "• Check your internet connection\n"
                "• Try a smaller image size\n\n"
                "If the problem persists, please contact support."
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_msg
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

async def post_init(application: Application):
    """Enhanced initialization after bot starts"""
    logger.info("🔄 Running post-initialization checks...")
    
    # Check Railway environment first
    await check_railway_environment()
    
    # Run Tesseract diagnostics
    await diagnose_tesseract_setup()
    
    # Check OCR engine status
    try:
        ocr_status = "✅ OCR Engine Ready"
        if hasattr(ocr_processor, 'engines'):
            active_engines = list(ocr_processor.engines.keys())
            ocr_status += f" | Engines: {active_engines}"
        logger.info(ocr_status)
    except Exception as e:
        logger.error(f"❌ OCR Engine check failed: {e}")
    
    # Check database connection
    try:
        if hasattr(db, 'is_mock'):
            if db.is_mock:
                logger.warning("⚠️ Using mock database - data will not persist")
            else:
                logger.info("✅ Database connection active")
        else:
            logger.info("✅ Database connection active")
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
    
    # Log available language count for user information
    available_count = len(ocr_processor.available_languages)
    logger.info(f"🌍 OCR Bot supports {available_count} languages")
    
    logger.info("🚀 Enhanced OCR Bot is ready!")

async def post_stop(application: Application):
    """Cleanup when bot stops"""
    logger.info("🛑 Bot is shutting down...")
    
    # Cleanup OCR resources
    try:
        if hasattr(ocr_processor, 'thread_pool'):
            ocr_processor.thread_pool.shutdown(wait=False)
            logger.info("✅ OCR thread pool shutdown")
    except Exception as e:
        logger.error(f"❌ OCR cleanup failed: {e}")
    
    logger.info("👋 Bot shutdown complete")

def main():
    """Enhanced main function with better error handling"""
    try:
        # Get bot token
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not found")
            return
        
        logger.info(f"✅ BOT_TOKEN found: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
        
        # Railway-specific logging
        logger.info("🚄 Starting Enhanced OCR Bot on Railway...")
        logger.info("📊 Environment: PRODUCTION")
        logger.info("🌍 Multi-language OCR Support")
        
        # Create application with enhanced settings
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(post_init)
            .post_stop(post_stop)
            .build()
        )
        
        # Store database in bot_data
        application.bot_data['db'] = db
        logger.info("✅ Database connected to bot data")
        
        # Enhanced handler registration with menu support
        handlers = [
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("settings", show_quick_settings),
            CommandHandler("stats", show_quick_statistics),
            CommandHandler("menu", show_enhanced_main_menu),
            CommandHandler("check", force_check_membership),
            
            MessageHandler(filters.PHOTO, handle_image),
            MessageHandler(filters.TEXT & filters.Regex('^(📸 Convert Image|⚙️ Settings|📊 Statistics|❓ Help|🔄 Restart Bot)$'), handle_quick_actions),
        ]
        
        for handler in handlers:
            application.add_handler(handler)
        
        # Enhanced callback handlers with better error handling
        callback_patterns = [
            ("check_membership", handle_membership_check),
            ("restart_bot", handle_start_callback),
            ("main_menu", show_main_menu),
            ("settings", show_settings_menu),
            ("statistics", show_statistics),
            ("help", handle_help_callback),
            ("convert_image", handle_convert_image),
            ("change_format", show_format_menu),
            ("set_format_", handle_format_change),
            ("contact_support", handle_help_callback),
            ("reformat_", handle_reformat),
            # Enhanced menu callbacks
            ("settings_format", show_format_menu),
            ("settings_language", show_settings_menu),
            ("settings_performance", show_settings_menu),
            ("help_usage", help_command),
            ("help_languages", help_command),
            ("help_troubleshoot", help_command),
            ("help_support", handle_help_callback),
        ]
        
        for pattern, handler in callback_patterns:
            application.add_handler(CallbackQueryHandler(handler, pattern=pattern))
        
        # Add OCR-specific callback handler
        application.add_handler(CallbackQueryHandler(handle_ocr_callback, pattern="^ocr_"))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered successfully")
        logger.info("🔧 Enhanced Features:")
        logger.info("   • Smart language detection")
        logger.info("   • Multi-strategy OCR for blurry images")
        logger.info("   • Advanced Amharic language support")
        logger.info("   • Enhanced text formatting")
        logger.info("   • Better error handling and user feedback")
        logger.info("   • Quick-access menu system")
        logger.info("   • Performance optimizations")
        
        # Start the bot with enhanced settings
        logger.info("🚀 Starting enhanced bot polling...")
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        logger.error("💥 Full crash details:", exc_info=True)
        
        # Attempt graceful shutdown
        try:
            if 'application' in locals():
                application.stop()
                application.shutdown()
        except:
            pass
        
        # Suggest solutions based on error type
        if "token" in str(e).lower():
            logger.error("🔑 BOT_TOKEN might be invalid. Please check your environment variables.")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            logger.error("🌐 Network connection issue. Please check your internet connection.")
        elif "tesseract" in str(e).lower():
            logger.error("🔤 Tesseract OCR issue. Please check if Tesseract is installed correctly.")
        else:
            logger.error("💡 Check the logs above for specific error details.")

if __name__ == "__main__":
    # Enhanced startup with better resource management
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {e}")
        logger.error("Stack trace:", exc_info=True)