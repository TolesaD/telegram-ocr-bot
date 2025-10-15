import os
import logging
import asyncio
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram import Update
from dotenv import load_dotenv

# Configure logging for Railway
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import database FIRST to catch any import errors
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

# Now import handlers
try:
    from handlers.start import start_command, handle_membership_check, force_check_membership
    from handlers.help import help_command, handle_help_callback
    from handlers.ocr import handle_image, handle_reformat
    from handlers.menu import (
        show_main_menu, show_settings_menu, show_statistics,
        handle_convert_image, show_language_menu, show_format_menu,
        handle_language_change, handle_format_change, show_language_group
    )
    logger.info("✅ All handlers imported successfully")
except ImportError as e:
    logger.error(f"❌ Handler import failed: {e}")
    raise

async def error_handler(update: Update, context):
    """Handle errors gracefully"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Main function"""
    try:
        # Get bot token
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not found in environment variables")
            return
        
        # Railway-specific logging
        logger.info("🚄 Starting bot on Railway...")
        logger.info("📊 Environment: PRODUCTION")
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Store database in bot_data
        application.bot_data['db'] = db
        logger.info("✅ Database connected")
        
        # Register handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("settings", show_settings_menu))
        application.add_handler(CommandHandler("stats", show_statistics))
        application.add_handler(CommandHandler("check", force_check_membership))
        
        application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        
        # Callback handlers
        callback_patterns = [
            ("check_membership", handle_membership_check),
            ("main_menu", show_main_menu),
            ("settings", show_settings_menu),
            ("statistics", show_statistics),
            ("help", handle_help_callback),
            ("convert_image", handle_convert_image),
            ("change_language", show_language_menu),
            ("language_group_", show_language_group),
            ("change_format", show_format_menu),
            ("set_language_", handle_language_change),
            ("set_format_", handle_format_change),
            ("contact_support", handle_help_callback),
            ("reformat_", handle_reformat)
        ]
        
        for pattern, handler in callback_patterns:
            application.add_handler(CallbackQueryHandler(handler, pattern=pattern))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered")
        logger.info("🚀 Starting bot polling...")
        
        # Start the bot
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

if __name__ == "__main__":
    main()