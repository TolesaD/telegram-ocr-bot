#!/usr/bin/env python3
"""
Telegram Image-to-Text Converter Bot
Railway Optimized Version
"""
import os
import logging
import sys
import asyncio
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate that all required environment variables are set"""
    logger.info("🔍 Validating environment variables...")
    
    # Check BOT_TOKEN
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is not set!")
        logger.error("💡 Please set BOT_TOKEN in Railway environment variables")
        
        # Debug: Show all available environment variables (excluding sensitive ones)
        env_vars = {k: v for k, v in os.environ.items() if 'TOKEN' not in k and 'KEY' not in k and 'SECRET' not in k and 'PASSWORD' not in k}
        logger.info(f"📋 Available environment variables: {list(env_vars.keys())}")
        
        return False
    
    logger.info(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    
    # Check other optional variables
    MONGODB_URI = os.getenv('MONGODB_URI')
    if MONGODB_URI:
        logger.info(f"✅ MONGODB_URI: {MONGODB_URI[:20]}...")
    else:
        logger.warning("⚠️ MONGODB_URI not set, using mock database")
    
    SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'tolesadebushe9@gmail.com')
    logger.info(f"✅ SUPPORT_EMAIL: {SUPPORT_EMAIL}")
    
    # Check if running on Railway
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        logger.info(f"✅ Running on Railway: {os.getenv('RAILWAY_ENVIRONMENT')}")
    
    return True

async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown callback queries"""
    query = update.callback_query
    await query.answer()
    logger.warning(f"Unknown callback received: {query.data}")
    await query.edit_message_text(
        "❓ Unknown command. Please use the menu buttons.",
        parse_mode='Markdown'
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    try:
        if update and hasattr(update, 'effective_chat'):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Sorry, an error occurred. Please try again."
            )
    except Exception as e:
        logger.error(f"Error sending error message: {e}")

def setup_handlers(application):
    """Setup all bot handlers"""
    try:
        logger.info("🚀 Setting up bot handlers...")
        
        # Import handlers
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
        
        # Command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("settings", show_settings_menu))
        application.add_handler(CommandHandler("stats", show_statistics))
        application.add_handler(CommandHandler("check", force_check_membership))
        
        # Message handlers
        application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(handle_membership_check, pattern="^check_membership$"))
        application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
        application.add_handler(CallbackQueryHandler(show_settings_menu, pattern="^settings$"))
        application.add_handler(CallbackQueryHandler(show_statistics, pattern="^statistics$"))
        application.add_handler(CallbackQueryHandler(handle_help_callback, pattern="^help$"))
        application.add_handler(CallbackQueryHandler(handle_convert_image, pattern="^convert_image$"))
        application.add_handler(CallbackQueryHandler(show_language_menu, pattern="^change_language$"))
        application.add_handler(CallbackQueryHandler(show_language_group, pattern="^language_group_"))
        application.add_handler(CallbackQueryHandler(show_format_menu, pattern="^change_format$"))
        application.add_handler(CallbackQueryHandler(handle_language_change, pattern="^set_language_"))
        application.add_handler(CallbackQueryHandler(handle_format_change, pattern="^set_format_"))
        application.add_handler(CallbackQueryHandler(handle_help_callback, pattern="^contact_support$"))
        application.add_handler(CallbackQueryHandler(handle_reformat, pattern="^reformat_"))
        application.add_handler(CallbackQueryHandler(handle_unknown_callback))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        logger.info("✅ All bot handlers registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup handlers: {e}", exc_info=True)
        return False

async def test_bot_connection(application):
    """Test if bot can connect to Telegram"""
    try:
        bot = application.bot
        me = await bot.get_me()
        logger.info(f"✅ Bot connected: @{me.username} ({me.first_name})")
        return True
    except Exception as e:
        logger.error(f"❌ Bot connection failed: {e}")
        return False

async def main_async():
    """Async main function to start the bot"""
    try:
        logger.info("🤖 Starting Telegram Image-to-Text Converter Bot...")
        
        # Validate environment first
        if not validate_environment():
            logger.error("❌ Environment validation failed, exiting...")
            return 1
        
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Test bot connection
        connection_ok = await test_bot_connection(application)
        if not connection_ok:
            logger.error("❌ Bot connection test failed, exiting...")
            return 1
        
        # Setup handlers
        if not setup_handlers(application):
            logger.error("❌ Handler setup failed, exiting...")
            return 1
        
        logger.info("🚀 Starting bot in polling mode...")
        
        # Start the bot using the proper async approach
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info("✅ Bot is now running and ready to receive messages...")
        
        # Keep the bot running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup when bot stops
        try:
            if 'application' in locals():
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("✅ Bot stopped gracefully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main function to start the bot"""
    # Only load .env file if we're not on Railway and the file exists
    is_railway = 'RAILWAY_ENVIRONMENT' in os.environ
    has_dotenv = os.path.exists('.env')
    
    if not is_railway and has_dotenv:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("✅ Loaded environment variables from .env file (local development)")
        except ImportError:
            logger.info("ℹ️ python-dotenv not available, using system environment variables")
    elif is_railway:
        logger.info("🚄 Running on Railway - using system environment variables")
    else:
        logger.info("ℹ️ Using system environment variables")
    
    # Set up proper event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        # Run the async main function
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Unexpected error in main: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())