#!/usr/bin/env python3
"""
🎯 ImageToText Pro Bot - Production Ready for Railway
Advanced OCR Telegram Bot with Multi-Engine Support
"""
import os
import logging
import asyncio
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

# Production logging configuration
class ProductionFormatter(logging.Formatter):
    """Production formatter with emoji support"""
    def format(self, record):
        original = super().format(record)
        # Add production prefix
        if record.levelname == 'INFO':
            return f"📊 {original}"
        elif record.levelname == 'WARNING':
            return f"⚠️ {original}"
        elif record.levelname == 'ERROR':
            return f"❌ {original}"
        elif record.levelname == 'DEBUG':
            return f"🔍 {original}"
        return original

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('production.log', encoding='utf-8')
    ]
)

# Apply production formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(ProductionFormatter())

logger = logging.getLogger(__name__)

class ProductionConfig:
    """Production configuration"""
    BOT_NAME = "🎯 ImageToText Pro"
    VERSION = "2.1.0"
    SUPPORT_EMAIL = "tolesadebushe9@gmail.com"
    CHANNEL = "@ImageToTextConverter"
    MAX_CONCURRENT_USERS = 100
    REQUEST_TIMEOUT = 30
    MAX_IMAGE_SIZE = 15 * 1024 * 1024  # 15MB

def validate_production_environment():
    """Validate production environment variables"""
    logger.info("🔍 Validating production environment...")
    
    required_vars = ['BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Log configuration (safely)
    bot_token = os.getenv('BOT_TOKEN', '')
    logger.info(f"✅ BOT_TOKEN: {bot_token[:10]}...{bot_token[-10:]}")
    logger.info(f"✅ Database: {'MongoDB' if os.getenv('MONGODB_URI') else 'Production Mock'}")
    logger.info(f"✅ Support: {ProductionConfig.SUPPORT_EMAIL}")
    logger.info(f"✅ Channel: {ProductionConfig.CHANNEL}")
    logger.info(f"✅ Version: {ProductionConfig.VERSION}")
    
    return True

def setup_production_database():
    """Setup production database with Railway compatibility"""
    from database.mongodb import db
    
    if db.is_mock:
        logger.info("🔄 Using production mock database")
    else:
        logger.info("🔄 Using MongoDB Atlas")
    
    return db

async def production_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Production error handler"""
    logger.error("🚨 Production error occurred:", exc_info=context.error)
    
    try:
        if update and hasattr(update, 'effective_chat'):
            error_message = (
                "❌ *System Temporarily Unavailable*\n\n"
                "Our system encountered an unexpected error. "
                "The technical team has been notified.\n\n"
                "Please try again in a few moments."
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

async def production_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown callbacks in production"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 *Unknown Command*\n\n"
        "This button is no longer active. Please use the current menu options.",
        parse_mode='Markdown'
    )

async def test_production_connection(application):
    """Test production bot connection"""
    try:
        bot = application.bot
        me = await asyncio.wait_for(bot.get_me(), timeout=10.0)
        
        logger.info(f"✅ Production Bot: @{me.username}")
        logger.info(f"✅ Bot Name: {me.first_name}")
        logger.info(f"✅ Bot ID: {me.id}")
        
        return True
    except asyncio.TimeoutError:
        logger.error("❌ Bot connection timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Bot connection failed: {e}")
        return False

def setup_production_handlers(application):
    """Setup production handlers"""
    try:
        logger.info("🚀 Setting up production handlers...")
        
        # Import production handlers
        try:
            from handlers.start import start_command, handle_membership_check, force_check_membership
            from handlers.help import help_command, handle_help_callback
            from handlers.ocr import handle_image, handle_reformat
            from handlers.menu import (
                show_main_menu, 
                show_settings_menu, 
                show_statistics,
                handle_convert_image,
                show_language_menu,
                show_format_menu,
                handle_language_change,
                handle_format_change,
                show_language_group
            )
        except ImportError as e:
            logger.error(f"❌ Handler import failed: {e}")
            return False
        
        # Production command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("settings", show_settings_menu))
        application.add_handler(CommandHandler("stats", show_statistics))
        application.add_handler(CommandHandler("check", force_check_membership))
        
        # Production message handlers
        application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        
        # Production callback handlers
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
        
        # Unknown callback handler
        application.add_handler(CallbackQueryHandler(production_unknown_callback))
        
        # Production error handler
        application.add_error_handler(production_error_handler)
        
        logger.info(f"✅ Production handlers registered: {len(callback_patterns)} patterns")
        return True
        
    except Exception as e:
        logger.error(f"❌ Handler setup failed: {e}")
        return False

async def production_main():
    """Production main function"""
    try:
        # Production banner
        logger.info("🎯" + "="*60)
        logger.info(f"🚀 {ProductionConfig.BOT_NAME} v{ProductionConfig.VERSION}")
        logger.info("🎯" + "="*60)
        
        # Validate environment
        if not validate_production_environment():
            logger.error("❌ Production environment validation failed")
            return 1
        
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not found")
            return 1
        
        # Setup production database
        db = setup_production_database()
        
        # Create production application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Store database in bot_data for handlers to access
        application.bot_data['db'] = db
        
        # Test production connection
        if not await test_production_connection(application):
            logger.error("❌ Production connection test failed")
            return 1
        
        # Setup production handlers
        if not setup_production_handlers(application):
            logger.error("❌ Production handler setup failed")
            return 1
        
        # Start production bot
        logger.info("🎯 Starting production bot...")
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=0.5,
            timeout=10
        )
        
        # Production ready message
        logger.info("🎉" + "="*60)
        logger.info("✅ PRODUCTION BOT IS NOW LIVE ON RAILWAY!")
        logger.info(f"📊 Max concurrent users: {ProductionConfig.MAX_CONCURRENT_USERS}")
        logger.info(f"⏱️ Request timeout: {ProductionConfig.REQUEST_TIMEOUT}s")
        logger.info(f"📸 Max image size: {ProductionConfig.MAX_IMAGE_SIZE // 1024 // 1024}MB")
        logger.info("🎉" + "="*60)
        
        # Production monitoring loop
        startup_time = asyncio.get_event_loop().time()
        request_count = 0
        
        while True:
            await asyncio.sleep(300)  # 5 minutes
            uptime = asyncio.get_event_loop().time() - startup_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            
            logger.info(f"📈 Production uptime: {hours}h {minutes}m - Requests: {request_count}")
            
    except KeyboardInterrupt:
        logger.info("🛑 Production bot stopped by operator")
    except Exception as e:
        logger.error(f"🚨 Production crash: {e}", exc_info=True)
        return 1
    finally:
        # Graceful shutdown
        try:
            if 'application' in locals():
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("✅ Production shutdown completed")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
    
    return 0

def main():
    """Production entry point"""
    # Remove this line - don't load .env in production
    # from dotenv import load_dotenv
    # load_dotenv()
    
    # Windows compatibility
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        return asyncio.run(production_main())
    except KeyboardInterrupt:
        logger.info("🛑 Production interrupted")
        return 0
    except Exception as e:
        logger.error(f"🚨 Production fatal error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())