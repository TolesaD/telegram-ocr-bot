# handlers/help.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
import logging

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    keyboard = [
        [InlineKeyboardButton("📸 How to Use", callback_data="help_usage")],
        [InlineKeyboardButton("🌐 Supported Languages", callback_data="help_languages")],
        [InlineKeyboardButton("📝 Formats", callback_data="help_formats")],
        [InlineKeyboardButton("📩 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "❓ *Help Center*\n\n"
        "Welcome to the Image-to-Text Converter Bot! Select an option to learn more:\n\n"
        "• 📸 *How to Use*: Learn how to convert images\n"
        "• 🌐 *Supported Languages*: Over 100 languages supported\n"
        "• 📝 *Formats*: Available text output formats\n"
        "• 📩 *Contact Support*: Get help from our team"
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
            "1. Send an image containing text\n"
            "2. The bot automatically detects the language\n"
            "3. Choose your preferred format (Plain, HTML(Copy Code))\n"
            "4. Get the extracted text!\n\n"
            "💡 *Tips for Best Results*:\n"
            "• Use clear, well-lit images\n"
            "• Ensure text is focused\n"
            "• High contrast works best\n"
            "• Crop to text area"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "help_languages":
        text = (
            "🌐 *Supported Languages*\n\n"
            "The bot supports over 100 languages with automatic detection, including:\n"
            "• European: English, Spanish, French, etc.\n"
            "• Asian: Chinese, Japanese, Korean, etc.\n"
            "• Middle Eastern: Arabic, Hebrew, etc.\n"
            "• African: Amharic, Swahili, Yoruba, etc.\n"
            "• Indian: Hindi, Tamil, Telugu, etc.\n\n"
            "Just send your image, and we'll detect the language automatically!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "help_formats":
        text = (
            "📝 *Available Formats*\n\n"
            "Choose how you want your text output:\n"
            "• 📄 *Plain*: Simple text without formatting\n"
            "• 🌐 *HTML(Copy Code)*: Text with HTML tags for web use\n\n"
            "Change format in Settings!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif callback_data == "contact_support":
        text = (
            "📩 *Contact Support*\n\n"
            f"Need help? Contact our support team via our Telegram Support Bot:\n"
            f"👉 {config.SUPPORT_BOT}\n\n"
            "Please provide:\n"
            "• A description of your issue\n"
            "• The image you tried (if applicable)\n"
            "• Any error messages you received"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
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