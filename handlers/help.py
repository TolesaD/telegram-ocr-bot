from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.mongodb import db
import config  # CHANGED FROM config_optimized to config
import logging

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "🤖 *Image to Text Converter Bot - Help*\n\n"
        "📸 *How to Use:*\n"
        "1. Send me an image containing text\n"
        "2. I'll automatically extract the text\n"
        "3. Choose your preferred text format\n\n"
        "⚙️ *Settings:*\n"
        "• Change OCR language\n"
        "• Set default text format\n\n"
        "🌐 *Supported Languages:*\n"
        "English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi\n\n"
        "📝 *Output Formats:*\n"
        "• Plain Text\n"
        "• Markdown\n"
        "• HTML\n\n"
        "❓ *Need Help?*\n"
        "Contact support via email for assistance."
    )
    
    keyboard = [
        [InlineKeyboardButton("📧 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help menu callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "contact_support":
        support_text = (
            f"📧 *Contact Support*\n\n"
            f"For assistance, please email:\n"
            f"`{config.Config.SUPPORT_EMAIL}`\n\n"
            f"Please include:\n"
            f"• Your username\n"
            f"• Description of the issue\n"
            f"• Screenshots if applicable"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Help", callback_data="help")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(support_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "help":
        await help_callback(update, context)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help menu via callback"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "🤖 *Image to Text Converter Bot - Help*\n\n"
        "📸 *How to Use:*\n"
        "1. Send me an image containing text\n"
        "2. I'll automatically extract the text\n"
        "3. Choose your preferred text format\n\n"
        "Need more help? Contact support!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📧 Contact Support", callback_data="contact_support")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
