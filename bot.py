#!/usr/bin/env python3
"""
Telegram Image-to-Text Converter Bot - Railway Optimized
"""
import os
import logging
import asyncio
import sys
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

# Enhanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_mock_database():
    """Create a simple mock database when MongoDB is not available"""
    logger.info("🔄 Setting up mock database...")
    
    class MockCollection:
        def __init__(self, name):
            self.name = name
            self.data = {}
        
        def insert_one(self, document):
            doc_id = str(len(self.data) + 1)
            self.data[doc_id] = document
            return type('Result', (), {'inserted_id': doc_id})
        
        def find_one(self, query=None):
            if not self.data:
                return None
            return list(self.data.values())[-1]  # Return last inserted
        
        def update_one(self, query, update, upsert=False):
            if '$set' in update:
                for key, value in update['$set'].items():
                    if self.data:
                        last_key = list(self.data.keys())[-1]
                        self.data[last_key][key] = value
            return type('Result', (), {'matched_count': 1, 'modified_count': 1})
        
        def count_documents(self, query=None):
            return len(self.data)
    
    class MockDatabase:
        def __init__(self):
            self.collections = {}
        
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MockCollection(name)
            return self.collections[name]
    
    logger.info("✅ Mock database setup complete")
    return MockDatabase()

def validate_environment():
    """Validate that all required environment variables are set"""
    logger.info("🔍 Validating environment variables...")
    
    # Check BOT_TOKEN
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is not set!")
        logger.error("💡 Please set BOT_TOKEN in Railway environment variables")
        return False
    
    logger.info(f"✅ BOT_TOKEN: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    
    # Check MONGODB_URI (optional but recommended)
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        logger.warning("⚠️ MONGODB_URI not set, using mock database")
    else:
        logger.info(f"✅ MONGODB_URI: {MONGODB_URI[:20]}...")
    
    # Check SUPPORT_EMAIL
    SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'tolesadebushe9@gmail.com')
    logger.info(f"✅ SUPPORT_EMAIL: {SUPPORT_EMAIL}")
    
    return True

def setup_database():
    """Setup database connection with improved error handling"""
    try:
        MONGODB_URI = os.getenv('MONGODB_URI')
        if not MONGODB_URI:
            logger.warning("⚠️ MONGODB_URI not set, using mock database")
            return setup_mock_database()
        
        import pymongo
        from pymongo.errors import ConnectionFailure
        
        # Try multiple connection strategies
        connection_strategies = [
            # Strategy 1: Standard connection with SSL
            {
                'tls': True,
                'tlsAllowInvalidCertificates': False,
                'retryWrites': True,
                'w': 'majority'
            },
            # Strategy 2: Without SSL (for local development)
            {
                'tls': False,
                'retryWrites': True,
                'w': 'majority'
            },
            # Strategy 3: Allow invalid certificates
            {
                'tls': True,
                'tlsAllowInvalidCertificates': True,
                'retryWrites': True,
                'w': 'majority'
            }
        ]
        
        client = None
        last_error = None
        
        for i, strategy in enumerate(connection_strategies):
            try:
                logger.info(f"🔄 Trying MongoDB connection strategy {i + 1}...")
                
                client = pymongo.MongoClient(
                    MONGODB_URI,
                    connectTimeoutMS=30000,
                    socketTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                    **strategy
                )
                
                # Test the connection
                client.admin.command('ismaster')
                db = client.get_database()
                logger.info(f"✅ MongoDB connection established successfully with strategy {i + 1}")
                return db
                
            except Exception as e:
                last_error = e
                logger.warning(f"❌ MongoDB connection strategy {i + 1} failed: {str(e)[:100]}...")
                if client:
                    client.close()
                continue
        
        # If all strategies fail
        logger.error(f"❌ All MongoDB connection strategies failed. Last error: {last_error}")
        logger.info("🔄 Falling back to mock database...")
        return setup_mock_database()
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        logger.info("🔄 Setting up mock database...")
        return setup_mock_database()

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

def setup_handlers(application, db):
    """Setup all bot handlers"""
    try:
        logger.info("🚀 Setting up bot handlers...")
        
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
            logger.error(f"❌ Failed to import handlers: {e}")
            # Create fallback handlers
            async def fallback_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text("🤖 Bot is starting up. Please try again in a moment.")
            
            async def fallback_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text("📖 Help is not available at the moment. Please try again later.")
            
            async def fallback_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text("🖼️ Image processing is temporarily unavailable.")
            
            # Use fallback handlers
            application.add_handler(CommandHandler("start", fallback_start))
            application.add_handler(CommandHandler("help", fallback_help))
            application.add_handler(MessageHandler(filters.PHOTO, fallback_image))
            application.add_handler(CallbackQueryHandler(handle_unknown_callback))
            application.add_error_handler(error_handler)
            logger.warning("⚠️ Using fallback handlers due to import errors")
            return True
        
        # Command handlers
        application.add_handler(CommandHandler("start", lambda u, c: start_command(u, c, db)))
        application.add_handler(CommandHandler("help", lambda u, c: help_command(u, c, db)))
        application.add_handler(CommandHandler("settings", lambda u, c: show_settings_menu(u, c, db)))
        application.add_handler(CommandHandler("stats", lambda u, c: show_statistics(u, c, db)))
        application.add_handler(CommandHandler("check", lambda u, c: force_check_membership(u, c, db)))
        
        # Message handlers
        application.add_handler(MessageHandler(filters.PHOTO, lambda u, c: handle_image(u, c, db)))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_membership_check(u, c, db), pattern="^check_membership$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: show_main_menu(u, c, db), pattern="^main_menu$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: show_settings_menu(u, c, db), pattern="^settings$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: show_statistics(u, c, db), pattern="^statistics$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_help_callback(u, c, db), pattern="^help$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_convert_image(u, c, db), pattern="^convert_image$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: show_language_menu(u, c, db), pattern="^change_language$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: show_language_group(u, c, db), pattern="^language_group_"))
        application.add_handler(CallbackQueryHandler(lambda u, c: show_format_menu(u, c, db), pattern="^change_format$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_language_change(u, c, db), pattern="^set_language_"))
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_format_change(u, c, db), pattern="^set_format_"))
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_help_callback(u, c, db), pattern="^contact_support$"))
        application.add_handler(CallbackQueryHandler(lambda u, c: handle_reformat(u, c, db), pattern="^reformat_"))
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
        logger.info("🤖 Starting Telegram Image-to-Text Converter Bot on Railway...")
        
        # Validate environment first
        if not validate_environment():
            logger.error("❌ Environment validation failed, exiting...")
            return 1
        
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        
        # Setup database
        db = setup_database()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Test bot connection
        connection_ok = await test_bot_connection(application)
        if not connection_ok:
            logger.error("❌ Bot connection test failed, exiting...")
            return 1
        
        # Setup handlers
        if not setup_handlers(application, db):
            logger.error("❌ Handler setup failed, exiting...")
            return 1
        
        logger.info("🚀 Starting bot in polling mode...")
        
        # Initialize and start the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info("✅ Bot is now running and ready to receive messages...")
        
        # Keep the bot running until stopped
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
    """Main function to start the bot with proper event loop handling"""
    from dotenv import load_dotenv
    load_dotenv()
    
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