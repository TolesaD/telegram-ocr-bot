from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config  # Import config directly
from database.mongodb import db

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("📷 Convert Image to Text", callback_data="convert_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Add database status to menu
    db_status = "⚠️ Temporary Storage" if db.is_mock else "✅ Database Connected"
    
    message_text = (
        f"🤖 *Image to Text Converter Bot*\n\n"
        f"*Status:* {db_status}\n\n"
        "I can extract text from images using OCR technology.\n\n"
        "Please choose an option:"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message_text, 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    user_id = update.callback_query.from_user.id
    
    try:
        user = db.get_user(user_id)
        if user and 'settings' in user:
            user_settings = user['settings']
        else:
            # Default settings if user not found
            user_settings = {
                'language': 'english',
                'text_format': 'plain'
            }
    except Exception as e:
        print(f"Error getting user settings: {e}")
        user_settings = {
            'language': 'english', 
            'text_format': 'plain'
        }
    
    current_language = user_settings.get('language', 'english')
    current_format = user_settings.get('text_format', 'plain')
    
    keyboard = [
        [InlineKeyboardButton(f"🌐 Language: {current_language.title()}", callback_data="change_language")],
        [InlineKeyboardButton(f"📝 Format: {current_format.upper()}", callback_data="change_format")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"⚙️ *Settings*\n\n"
        f"Current Settings:\n"
        f"• Language: {current_language.title()}\n"
        f"• Text Format: {current_format.upper()}\n\n"
        f"Choose a setting to change:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )