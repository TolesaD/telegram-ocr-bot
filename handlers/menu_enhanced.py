# handlers/menu_enhanced.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from utils.text_formatter import TextFormatter

logger = logging.getLogger(__name__)

# Persistent menu keyboard
def get_main_menu_keyboard():
    """Get the main menu keyboard"""
    keyboard = [
        [KeyboardButton("📸 Convert Image"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("📊 Statistics"), KeyboardButton("❓ Help")],
        [KeyboardButton("🔄 Restart Bot")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

async def show_enhanced_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show enhanced main menu with quick actions"""
    try:
        user = update.effective_user
        welcome_text = (
            f"👋 Welcome *{user.first_name}*!\n\n"
            "🚀 *Image to Text Converter Bot*\n\n"
            "📋 *Quick Actions:*\n"
            "• 📸 Convert Image - Extract text from images\n"
            "• ⚙️ Settings - Configure OCR preferences\n"
            "• 📊 Statistics - View your usage stats\n"
            "• ❓ Help - Get assistance\n\n"
            "💡 *Tip:* Just send me an image or use the menu below!"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        logger.info(f"📱 Enhanced menu shown for user {user.id}")
        
    except Exception as e:
        logger.error(f"Error showing enhanced menu: {e}")
        await update.message.reply_text(
            "🚀 Welcome! Use the menu below to get started.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_quick_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick actions from the menu"""
    text = update.message.text
    
    if text == "📸 Convert Image":
        await handle_convert_image_quick(update, context)
    elif text == "⚙️ Settings":
        await show_quick_settings(update, context)
    elif text == "📊 Statistics":
        await show_quick_statistics(update, context)
    elif text == "❓ Help":
        await show_quick_help(update, context)
    elif text == "🔄 Restart Bot":
        await restart_bot_quick(update, context)

async def handle_convert_image_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick convert image handler"""
    await update.message.reply_text(
        "📸 *Ready to convert!*\n\n"
        "Just send me an image and I'll extract the text from it.\n\n"
        "💡 *Tips for best results:*\n"
        "• Use clear, well-lit images\n"
        "• Ensure text is readable\n"
        "• Avoid blurry or angled photos\n"
        "• Supported: 100+ languages including Amharic 🇪🇹",
        parse_mode='Markdown'
    )

async def show_quick_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick settings menu"""
    keyboard = [
        [InlineKeyboardButton("🔤 Text Format", callback_data="settings_format")],
        [InlineKeyboardButton("🌍 Language", callback_data="settings_language")],
        [InlineKeyboardButton("⚡ Performance", callback_data="settings_performance")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ *Settings*\n\n"
        "Configure your OCR preferences:\n\n"
        "• 🔤 Text Format - Choose how text is formatted\n"
        "• 🌍 Language - Set preferred languages\n"
        "• ⚡ Performance - Optimize processing speed\n",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_quick_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick statistics display"""
    try:
        user_id = update.effective_user.id
        db = context.bot_data.get('db')
        
        if db and hasattr(db, 'get_user_stats'):
            stats = db.get_user_stats(user_id)
            total_requests = stats.get('total_requests', 0)
            recent_requests = stats.get('recent_requests', [])
            
            stats_text = (
                f"📊 *Your Statistics*\n\n"
                f"• Total Requests: *{total_requests}*\n"
                f"• Recent Activity: *{len(recent_requests)}* requests\n\n"
            )
            
            if recent_requests:
                stats_text += "📈 *Recent Activity:*\n"
                for req in recent_requests[:3]:  # Show last 3 requests
                    lang = req.get('language', 'Unknown')
                    status = "✅" if req.get('success') else "❌"
                    stats_text += f"  {status} {lang.upper()} - {req.get('timestamp', '')}\n"
        else:
            stats_text = "📊 *Statistics*\n\nNo data available yet. Start converting images to see your stats!"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await update.message.reply_text(
            "📊 *Statistics*\n\nUnable to load statistics at the moment.",
            parse_mode='Markdown'
        )

async def show_quick_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick help menu"""
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data="help_usage")],
        [InlineKeyboardButton("🌍 Languages", callback_data="help_languages")],
        [InlineKeyboardButton("🔧 Troubleshooting", callback_data="help_troubleshoot")],
        [InlineKeyboardButton("📞 Contact Support", callback_data="help_support")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "❓ *Help Center*\n\n"
        "Get help with using the bot:\n\n"
        "• 📖 How to Use - Basic instructions\n"
        "• 🌍 Languages - Supported languages\n"
        "• 🔧 Troubleshooting - Common issues\n"
        "• 📞 Contact Support - Get help from humans\n",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def restart_bot_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick restart handler"""
    from handlers.start import start_command
    await start_command(update, context)