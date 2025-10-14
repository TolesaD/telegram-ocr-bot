#!/usr/bin/env python3
"""
🎯 ImageToText Pro Bot - Railway Optimized
Advanced OCR Telegram Bot with Multi-Engine Support
"""
import os
import logging
import asyncio
import sys

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/production.log')  # Railway compatible path
    ]
)

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

def validate_railway_environment():
    """Validate Railway environment variables"""
    logger.info("🔍 Validating Railway environment...")
    
    # Check BOT_TOKEN first (most critical)
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        logger.info("💡 Please add BOT_TOKEN in Railway Variables tab")
        return False
    
    # Log available environment variables (safely)
    env_vars = {
        'BOT_TOKEN': f"{BOT_TOKEN[:8]}...{BOT_TOKEN[-8:]}" if BOT_TOKEN else 'Not set',
        'MONGODB_URI': 'Set' if os.getenv('MONGODB_URI') else 'Not set',
        'SUPPORT_EMAIL': os.getenv('SUPPORT_EMAIL', 'Not set'),
        'ADMIN_IDS': 'Set' if os.getenv('ADMIN_IDS') else 'Not set'
    }
    
    logger.info("📋 Environment variables:")
    for key, value in env_vars.items():
        logger.info(f"   {key}: {value}")
    
    return True

def setup_railway_database():
    """Setup database for Railway"""
    from database.mongodb import db
    
    if db.is_mock:
        logger.info("🔄 Using production mock database on Railway")
    else:
        logger.info("🔄 Using MongoDB Atlas on Railway")
    
    return db

async def railway_error_handler(update: object, context):
    """Railway error handler"""
    logger.error("🚨 Railway error:", exc_info=context.error)

async def test_railway_connection(application):
    """Test bot connection on Railway"""
    try:
        bot = application.bot
        me = await asyncio.wait_for(bot.get_me(), timeout=10.0)
        
        logger.info(f"✅ Railway Bot: @{me.username}")
        logger.info(f"✅ Bot Name: {me.first_name}")
        logger.info(f"✅ Bot ID: {me.id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Railway connection failed: {e}")
        return False

def setup_railway_handlers(application):
    """Setup handlers for Railway"""
    try:
        logger.info("🚀 Setting up Railway handlers...")
        
        # Import handlers
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
        
        # Command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("settings", show_settings_menu))
        application.add_handler(CommandHandler("stats", show_statistics))
        application.add_handler(CommandHandler("check", force_check_membership))
        
        # Message handlers
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
        
        # Error handler
        application.add_error_handler(railway_error_handler)
        
        logger.info(f"✅ Railway handlers registered: {len(callback_patterns)} patterns")
        return True
        
    except Exception as e:
        logger.error(f"❌ Handler setup failed: {e}")
        return False

async def railway_main():
    """Main function for Railway"""
    try:
        # Railway banner
        logger.info("🚂" + "="*60)
        logger.info(f"🚀 {ProductionConfig.BOT_NAME} v{ProductionConfig.VERSION}")
        logger.info("🎯 DEPLOYED ON RAILWAY")
        logger.info("🚂" + "="*60)
        
        # Validate environment
        if not validate_railway_environment():
            logger.error("❌ Railway environment validation failed")
            return 1
        
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not available")
            return 1
        
        # Setup database
        db = setup_railway_database()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Store database in bot_data
        application.bot_data['db'] = db
        
        # Test connection
        if not await test_railway_connection(application):
            logger.error("❌ Railway connection test failed")
            return 1
        
        # Setup handlers
        if not setup_railway_handlers(application):
            logger.error("❌ Railway handler setup failed")
            return 1
        
        # Start bot
        logger.info("🎯 Starting Railway bot...")
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=1.0,
            timeout=25
        )
        
        # Railway ready message
        logger.info("🎉" + "="*60)
        logger.info("✅ RAILWAY BOT IS NOW LIVE!")
        logger.info(f"📊 Max concurrent users: {ProductionConfig.MAX_CONCURRENT_USERS}")
        logger.info(f"⏱️ Request timeout: {ProductionConfig.REQUEST_TIMEOUT}s")
        logger.info(f"📸 Max image size: {ProductionConfig.MAX_IMAGE_SIZE // 1024 // 1024}MB")
        logger.info("🌐 https://railway.app")
        logger.info("🎉" + "="*60)
        
        # Keep alive
        while True:
            await asyncio.sleep(3600)  # 1 hour
            
    except KeyboardInterrupt:
        logger.info("🛑 Railway bot stopped")
    except Exception as e:
        logger.error(f"🚨 Railway crash: {e}", exc_info=True)
        return 1
    finally:
        # Graceful shutdown
        try:
            if 'application' in locals():
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("✅ Railway shutdown completed")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
    
    return 0

def main():
    """Railway entry point"""
    # No dotenv on Railway - use environment variables directly
    try:
        return asyncio.run(railway_main())
    except KeyboardInterrupt:
        logger.info("🛑 Railway interrupted")
        return 0
    except Exception as e:
        logger.error(f"🚨 Railway fatal error: {e}")
        return 1

if __name__ == '__main__':
    # Import here to avoid circular imports
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, CallbackQueryHandler,
        ContextTypes, filters
    )
    
    sys.exit(main())