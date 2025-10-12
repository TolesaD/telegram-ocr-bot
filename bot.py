#!/usr/bin/env python3
"""
Telegram Image-to-Text Converter Bot
Main bot file with proper error handling and all callback handlers
"""
import os
import logging
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

class OCRBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers with proper error handling"""
        try:
            logger.info("Setting up bot handlers...")
            
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
                handle_format_change
            )
            
            # Command handlers
            self.application.add_handler(CommandHandler("start", start_command))
            self.application.add_handler(CommandHandler("help", help_command))
            self.application.add_handler(CommandHandler("settings", show_settings_menu))
            self.application.add_handler(CommandHandler("stats", show_statistics))
            self.application.add_handler(CommandHandler("check", force_check_membership))
            
            # Message handlers
            self.application.add_handler(MessageHandler(filters.PHOTO, handle_image))
            
            # Callback query handlers - ORDER MATTERS!
            # Specific patterns first, then generic ones
            
            # Channel membership
            self.application.add_handler(CallbackQueryHandler(handle_membership_check, pattern="^check_membership$"))
            
            # Main menu and navigation
            self.application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
            self.application.add_handler(CallbackQueryHandler(show_settings_menu, pattern="^settings$"))
            self.application.add_handler(CallbackQueryHandler(show_statistics, pattern="^statistics$"))
            self.application.add_handler(CallbackQueryHandler(handle_help_callback, pattern="^help$"))
            self.application.add_handler(CallbackQueryHandler(handle_convert_image, pattern="^convert_image$"))
            
            # Settings sub-menus
            self.application.add_handler(CallbackQueryHandler(show_language_menu, pattern="^change_language$"))
            self.application.add_handler(CallbackQueryHandler(show_format_menu, pattern="^change_format$"))
            self.application.add_handler(CallbackQueryHandler(handle_language_change, pattern="^set_language_"))
            self.application.add_handler(CallbackQueryHandler(handle_format_change, pattern="^set_format_"))
            
            # Help sub-menus
            self.application.add_handler(CallbackQueryHandler(handle_help_callback, pattern="^contact_support$"))
            
            # OCR reformatting
            self.application.add_handler(CallbackQueryHandler(handle_reformat, pattern="^reformat_"))
            
            # Fallback handler for unknown callbacks
            self.application.add_handler(CallbackQueryHandler(self.handle_unknown_callback))
            
            # Error handler
            self.application.add_error_handler(self.error_handler)
            
            logger.info("✅ All bot handlers registered successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup handlers: {e}")
            raise
    
    async def handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown callback queries"""
        query = update.callback_query
        await query.answer()
        logger.warning(f"Unknown callback received: {query.data}")
        await query.edit_message_text(
            "❓ Unknown command. Please use the menu buttons.",
            parse_mode='Markdown'
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Try to send a user-friendly error message if possible
        try:
            if update and hasattr(update, 'effective_chat'):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Sorry, an error occurred. Please try again."
                )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    def run(self, use_webhook=False):
        """Run the bot"""
        try:
            logger.info("Starting bot...")
            
            if use_webhook:
                # Webhook mode for production
                webhook_url = os.getenv('WEBHOOK_URL', '')
                if webhook_url:
                    self.application.run_webhook(
                        listen="0.0.0.0",
                        port=int(os.getenv('PORT', 8443)),
                        url_path=os.getenv('BOT_TOKEN'),
                        webhook_url=f"{webhook_url}/{os.getenv('BOT_TOKEN')}"
                    )
                else:
                    logger.warning("WEBHOOK_URL not set, falling back to polling")
                    self.application.run_polling()
            else:
                # Polling mode for development
                self.application.run_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES
                )
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Failed to run bot: {e}")
            raise

def main():
    """Main function to start the bot"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get bot token
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is not set")
        print("Please set BOT_TOKEN in your .env file")
        return
    
    # Check if running on PythonAnywhere
    ON_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ
    
    print(f"\n{'='*60}")
    print("🤖 Telegram Image-to-Text Converter Bot")
    print(f"{'='*60}")
    print(f"📍 Environment: {'PythonAnywhere' if ON_PYTHONANYWHERE else 'Local'}")
    print(f"🔑 Bot Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
    print(f"{'='*60}")
    
    try:
        # Initialize and run bot
        bot = OCRBot(BOT_TOKEN)
        
        # FORCE POLLING MODE - webhooks don't work well on PythonAnywhere free tier
        use_webhook = False
        
        if use_webhook:
            logger.info("Starting in webhook mode...")
        else:
            logger.info("Starting in polling mode...")
        
        bot.run(use_webhook=use_webhook)
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())