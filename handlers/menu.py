from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from database.mongodb import db
import config
import logging

logger = logging.getLogger(__name__)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the main menu"""
    keyboard = [
        [InlineKeyboardButton("📸 Convert Image", callback_data="convert_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🤖 *Main Menu*\n\nChoose an option:"
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.effective_message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu with user's current settings"""
    user_id = update.effective_user.id
    
    # Get user settings
    try:
        user = db.get_user(user_id)
        user_settings = user.get('settings', {}) if user else {}
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        user_settings = {}
    
    current_format = user_settings.get('text_format', 'plain')
    
    # Get display names
    format_display = current_format.upper()
    
    keyboard = [
        [InlineKeyboardButton(f"📝 Format: {format_display}", callback_data="change_format")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = (
        "⚙️ *Settings*\n\n"
        f"• 📝 *Current Format:* {format_display}\n\n"
        "Choose what you want to change:"
    )
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.effective_message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_format_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show text format selection menu (replaced markdown with copiable)"""
    user_id = update.effective_user.id
    
    # Get current format
    try:
        user = db.get_user(user_id)
        user_settings = user.get('settings', {}) if user else {}
        current_format = user_settings.get('text_format', 'plain')
    except Exception as e:
        current_format = 'plain'
    
    keyboard = [
        [
            InlineKeyboardButton("📄 Plain Text", callback_data="set_format_plain"),
            InlineKeyboardButton("📋 Copiable", callback_data="set_format_copiable")
        ],
        [
            InlineKeyboardButton("🌐 HTML", callback_data="set_format_html")
        ],
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    format_info = {
        'plain': "Simple text without formatting",
        'copiable': "Clean text optimized for easy copying",
        'html': "Text with HTML tags for web use"
    }
    
    text = (
        f"📝 *Text Format Selection*\n\n"
        f"Current: {current_format.upper()}\n\n"
        f"Choose your preferred text format:\n"
        f"• 📄 Plain: {format_info['plain']}\n"
        f"• 📋 Copiable: {format_info['copiable']}\n"
        f"• 🌐 HTML: {format_info['html']}"
    )
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.effective_message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_format_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format change"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    text_format = query.data.replace('set_format_', '')
    
    if text_format not in config.FORMAT_OPTIONS:
        await query.answer("❌ Format not supported")
        return
    
    # Update user settings
    try:
        user = db.get_user(user_id)
        if user:
            settings = user.get('settings', {})
            settings['text_format'] = text_format
            db.update_user_settings(user_id, settings)
        else:
            # Create new user with settings
            user_data = {
                'user_id': user_id,
                'settings': {'text_format': text_format}
            }
            db.insert_user(user_data)
        
        await query.answer(f"✅ Format set to {text_format.upper()}")
        
        # Return to settings menu
        await show_settings_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error updating format: {e}")
        await query.answer("❌ Error updating format")

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.effective_user.id
    
    try:
        stats = db.get_user_stats(user_id)
        total_requests = stats['total_requests']
        recent_requests = stats['recent_requests']
        
        stats_text = f"📊 *Your Statistics*\n\n• Total OCR Requests: {total_requests}\n\n"
        
        if recent_requests:
            stats_text += "📅 Recent Requests:\n"
            for req in recent_requests[:3]:  # Show last 3 requests
                timestamp = req.get('timestamp', 'Unknown')
                status = req.get('status', 'unknown')
                
                if isinstance(timestamp, str):
                    time_str = timestamp
                else:
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                
                status_icon = "✅" if status == 'success' else "❌"
                stats_text += f"{status_icon} {time_str}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.effective_message.reply_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        text = "❌ Error loading statistics"
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                text,
                parse_mode='Markdown'
            )
        else:
            await update.effective_message.reply_text(
                text,
                parse_mode='Markdown'
            )

async def handle_convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle convert image callback"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"📸 *Convert Image*\n\n"
        "Simply send me an image containing text and I'll extract it for you!\n\n"
        "💡 *Tips for best results:*\n"
        "• Use clear, well-lit images\n"
        "• Ensure text is focused\n"
        "• High contrast works best\n"
        "• Crop to text area"
    )
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.effective_message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Main callback handler that routes all menu callbacks
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all menu-related callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    logger.info(f"Menu callback: {callback_data}")
    
    if callback_data == "main_menu":
        await show_main_menu(update, context)
    elif callback_data == "convert_image":
        await handle_convert_image(update, context)
    elif callback_data == "settings":
        await show_settings_menu(update, context)
    elif callback_data == "statistics":
        await show_statistics(update, context)
    elif callback_data == "change_format":
        await show_format_menu(update, context)
    elif callback_data.startswith("set_format_"):
        await handle_format_change(update, context)
    else:
        logger.warning(f"Unknown menu callback: {callback_data}")
        await query.edit_message_text("❌ Unknown command. Returning to main menu.")
        await show_main_menu(update, context)