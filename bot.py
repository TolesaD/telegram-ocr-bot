import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Load environment variables
load_dotenv()

# Import handlers
from handlers.start import start_command
from handlers.help import help_command, handle_help_callback
from handlers.ocr import handle_image, handle_reformat
from handlers.menu import show_main_menu, show_settings_menu
from database.mongodb import db

class OCRBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
        self.application.add_handler(CallbackQueryHandler(show_settings_menu, pattern="^settings$"))
        self.application.add_handler(CallbackQueryHandler(handle_help_callback, pattern="^help$"))
        self.application.add_handler(CallbackQueryHandler(handle_help_callback, pattern="^contact_support$"))
        self.application.add_handler(CallbackQueryHandler(handle_reformat, pattern="^reformat_"))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot"""
        print(f"Exception while handling an update: {context.error}")
    
    def run(self):
        """Run the bot"""
        print("Bot is running...")
        self.application.run_polling()

def main():
    # Get bot token from environment
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is not set")
        return
    
    # Initialize and run bot
    bot = OCRBot(BOT_TOKEN)
    bot.run()

if __name__ == '__main__':
    main()