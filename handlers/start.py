from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from database.mongodb import db
from handlers.menu import show_main_menu

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    try:
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'settings': {
                'language': 'english',
                'text_format': 'plain',
                'updated_at': datetime.now()
            }
        }
        
        # Save user to database
        result = db.insert_user(user_data)
        
        if result:
            print(f"✅ User {user.id} saved to database")
        else:
            print(f"⚠️  User {user.id} not saved (using mock database)")
        
    except Exception as e:
        print(f"❌ Error saving user: {e}")
        # Continue even if user saving fails
    
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "🤖 *Welcome to Image to Text Converter Bot*\n\n"
        "I can extract text from images using advanced OCR technology.\n\n"
        "📸 *How to use:*\n"
        "1. Send me an image containing text\n"
        "2. I'll extract and send you the text\n"
        "3. Choose your preferred text format\n\n"
    )
    
    # Add database status to welcome message
    if db.is_mock:
        welcome_text += "\n\n"
    else:
        welcome_text += "✅ *Database:* Connected and saving your preferences\n\n"
    
    welcome_text += "Use the menu below to get started!"
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    await show_main_menu(update, context)