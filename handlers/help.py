# handlers/help.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    keyboard = [
        [InlineKeyboardButton("📸 How to Use", callback_data="help_usage")],
        [InlineKeyboardButton("🌐 Languages", callback_data="help_languages")],
        [InlineKeyboardButton("⚙️ Settings Guide", callback_data="help_settings")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "❓ *Help Center*\n\n"
        "Welcome to the Image-to-Text Converter Bot!\n\n"
        "Select an option to learn more about using the bot:"
    )
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.effective_message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help-related callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "help_usage":
        text = (
            "📸 *How to Use*\n\n"
            "1. *Send an Image* - Take a photo or upload any image with text\n"
            "2. *Auto Processing* - Bot detects language and extracts text automatically\n"
            "3. *Get Results* - Receive formatted text in seconds\n\n"
            "💡 *Pro Tips:*\n"
            "• Use clear, well-lit images for best accuracy\n"
            "• Ensure text is focused and readable\n"
            "• High contrast images work better\n"
            "• Horizontal text alignment is ideal\n\n"
            "🌍 *Automatic Language Detection*\n"
            "Supports 70+ languages including English, Spanish, French, German, Russian, Chinese, Japanese, Arabic, and many more!"
        )
        keyboard = [
            [InlineKeyboardButton("🌐 Languages", callback_data="help_languages")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "help_languages":
        text = (
            "🌐 *Supported Languages*\n\n"
            "The bot automatically detects and supports 70+ languages:\n\n"
            "*Major Languages:*\n"
            "• English, Spanish, French, German, Italian\n"
            "• Portuguese, Russian, Chinese, Japanese, Korean\n"
            "• Arabic, Hindi, Bengali, Turkish, Vietnamese\n"
            "• Thai, Hebrew, Greek, Dutch, Polish\n\n"
            "*African & Regional:*\n"
            "• Amharic, Swahili, Yoruba, Zulu, Afrikaans\n"
            "• Somali, Hausa, Igbo, Xhosa\n\n"
            "*And many more!*\n\n"
            "Just send your image - language detection is automatic!"
        )
        keyboard = [
            [InlineKeyboardButton("📸 How to Use", callback_data="help_usage")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "help_settings":
        text = (
            "⚙️ *Settings Guide*\n\n"
            "Customize your experience:\n\n"
            "📝 *Text Formats:*\n"
            "• 📄 Plain Text - Clean, readable text\n"
            "• 🌐 HTML Format - For web and apps\n\n"
            "📊 *Statistics:*\n"
            "• View your usage history\n"
            "• Track success rates\n"
            "• Monitor processing times\n\n"
            "Access settings via the main menu!"
        )
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "help":
        await help_command(update, context)
    
    else:
        logger.warning(f"Unknown help callback: {callback_data}")
        await query.edit_message_text("❌ Unknown command. Returning to help menu.")
        await help_command(update, context)