#!/usr/bin/env python3
"""
Local Testing Version - Telegram Image-to-Text Converter Bot
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

# Enhanced logging for local development
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_local_database():
    """Setup database for local testing"""
    logger.info("🔄 Setting up local database...")
    
    class LocalCollection:
        def __init__(self, name):
            self.name = name
            self.data = {}
            self.counter = 1
        
        def insert_one(self, document):
            doc_id = str(self.counter)
            self.data[doc_id] = document
            self.counter += 1
            return type('Result', (), {'inserted_id': doc_id})
        
        def find_one(self, query=None):
            if not query:
                return list(self.data.values())[-1] if self.data else None
            
            user_id = query.get('user_id')
            if user_id:
                for doc in self.data.values():
                    if doc.get('user_id') == user_id:
                        return doc
            return None
        
        def update_one(self, query, update, upsert=False):
            user_id = query.get('user_id')
            if user_id:
                # Find existing user
                for doc_id, doc in self.data.items():
                    if doc.get('user_id') == user_id:
                        if '$set' in update:
                            doc.update(update['$set'])
                        return type('Result', (), {'matched_count': 1, 'modified_count': 1})
                
                # If not found and upsert is True, create new
                if upsert:
                    new_doc = {'user_id': user_id}
                    if '$set' in update:
                        new_doc.update(update['$set'])
                    self.insert_one(new_doc)
                    return type('Result', (), {'matched_count': 0, 'modified_count': 0, 'upserted_id': 1})
            
            return type('Result', (), {'matched_count': 0, 'modified_count': 0})
        
        def count_documents(self, query=None):
            if not query:
                return len(self.data)
            
            user_id = query.get('user_id')
            if user_id:
                count = 0
                for doc in self.data.values():
                    if doc.get('user_id') == user_id:
                        count += 1
                return count
            return 0
    
    class LocalDatabase:
        def __init__(self):
            self.collections = {}
        
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = LocalCollection(name)
            return self.collections[name]
    
    logger.info("✅ Local database setup complete")
    return LocalDatabase()

async def main_local():
    """Main function for local testing"""
    try:
        logger.info("🤖 Starting Telegram Bot - LOCAL TESTING MODE...")
        
        # Check BOT_TOKEN
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not found in environment variables")
            logger.info("💡 Create a .env file with: BOT_TOKEN=your_bot_token_here")
            return 1
        
        # Setup local database (bypass MongoDB issues)
        db = setup_local_database()
        
        # Create application with longer timeouts
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Import and setup handlers
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
            return 1
        
        # Setup handlers
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
        
        # Error handler
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ All handlers registered successfully")
        
        # Start the bot
        logger.info("🚀 Starting bot in polling mode...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            timeout=10  # Shorter timeout for local testing
        )
        
        logger.info("✅ Bot is now running and ready to receive messages...")
        logger.info("💡 Press Ctrl+C to stop the bot")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        return 1
    finally:
        try:
            if 'application' in locals():
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    return 0

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # Set event loop policy for Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    sys.exit(asyncio.run(main_local()))