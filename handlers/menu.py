from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
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
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🤖 *Main Menu*\n\nChoose an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "🤖 *Main Menu*\n\nChoose an option:",
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
    
    current_language = user_settings.get('language', 'english')
    current_format = user_settings.get('text_format', 'plain')
    
    # Get display names
    language_display = config.LANGUAGE_DISPLAY_NAMES.get(current_language, current_language)
    format_display = current_format.upper()
    
    keyboard = [
        [InlineKeyboardButton(f"🌐 Language: {language_display}", callback_data="change_language")],
        [InlineKeyboardButton(f"📝 Format: {format_display}", callback_data="change_format")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = (
        "⚙️ *Settings*\n\n"
        f"• 🌐 *Current Language:* {language_display}\n"
        f"• 📝 *Current Format:* {format_display}\n\n"
        "Choose what you want to change:"
    )
    
    await update.callback_query.edit_message_text(
        settings_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu with organized groups"""
    user_id = update.effective_user.id
    
    # Get current language
    try:
        user = db.get_user(user_id)
        user_settings = user.get('settings', {}) if user else {}
        current_language = user_settings.get('language', 'english')
    except Exception as e:
        current_language = 'english'
    
    keyboard = []
    
    # European Languages
    keyboard.append([InlineKeyboardButton("🌍 European Languages", callback_data="language_group_european")])
    
    # Asian Languages  
    keyboard.append([InlineKeyboardButton("🌏 Asian Languages", callback_data="language_group_asian")])
    
    # Middle Eastern Languages
    keyboard.append([InlineKeyboardButton("🌐 Middle Eastern Languages", callback_data="language_group_middle_eastern")])
    
    # African Languages - ADDED THIS
    keyboard.append([InlineKeyboardButton("🌍 African Languages", callback_data="language_group_african")])
    
    # Indian Languages
    keyboard.append([InlineKeyboardButton("🇮🇳 Indian Languages", callback_data="language_group_indian")])
    
    # Back button
    keyboard.append([InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    current_lang_display = config.LANGUAGE_DISPLAY_NAMES.get(current_language, current_language)
    
    await update.callback_query.edit_message_text(
        f"🌐 *Language Selection*\n\n"
        f"Current: {current_lang_display}\n\n"
        "Choose a language group:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_language_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show languages in a specific group"""
    query = update.callback_query
    group_name = query.data.replace('language_group_', '')
    
    if group_name not in config.LANGUAGE_GROUPS:
        await query.answer("Invalid language group")
        return
    
    languages = config.LANGUAGE_GROUPS[group_name]
    
    if not languages:
        await query.answer("No languages available in this group")
        return
    
    keyboard = []
    
    # Add languages in rows of 2
    row = []
    for lang in languages:
        display_name = config.LANGUAGE_DISPLAY_NAMES.get(lang, lang)
        row.append(InlineKeyboardButton(display_name, callback_data=f"set_language_{lang}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:  # Add remaining buttons if any
        keyboard.append(row)
    
    # Back button
    keyboard.append([InlineKeyboardButton("🔙 Back to Language Groups", callback_data="change_language")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    group_display = group_name.replace('_', ' ').title()
    
    await query.edit_message_text(
        f"🌐 *{group_display}*\n\n"
        "Select your preferred language:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_language_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language change"""
    query = update.callback_query
    user_id = update.effective_user.id
    language = query.data.replace('set_language_', '')
    
    if language not in config.SUPPORTED_LANGUAGES:
        await query.answer("❌ Language not supported")
        return
    
    # Update user settings
    try:
        user = db.get_user(user_id)
        if user:
            settings = user.get('settings', {})
            settings['language'] = language
            db.update_user_settings(user_id, settings)
        else:
            # Create new user with settings
            user_data = {
                'user_id': user_id,
                'settings': {'language': language, 'text_format': 'plain'}
            }
            db.insert_user(user_data)
        
        language_display = config.LANGUAGE_DISPLAY_NAMES.get(language, language)
        await query.answer(f"✅ Language set to {language_display}")
        
        # Return to settings menu
        await show_settings_menu(update, context)
        
    except Exception as e:
        logger.error(f"Error updating language: {e}")
        await query.answer("❌ Error updating language")

async def show_format_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show text format selection menu"""
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
            InlineKeyboardButton("📋 Markdown", callback_data="set_format_markdown")
        ],
        [
            InlineKeyboardButton("🌐 HTML", callback_data="set_format_html")
        ],
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    format_info = {
        'plain': "Simple text without formatting",
        'markdown': "Formatted text for Markdown",
        'html': "Text with HTML tags"
    }
    
    await update.callback_query.edit_message_text(
        f"📝 *Text Format Selection*\n\n"
        f"Current: {current_format.upper()}\n\n"
        f"Choose your preferred text format:\n"
        f"• 📄 Plain: {format_info['plain']}\n"
        f"• 📋 Markdown: {format_info['markdown']}\n"  
        f"• 🌐 HTML: {format_info['html']}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_format_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format change"""
    query = update.callback_query
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
                'settings': {'language': 'english', 'text_format': text_format}
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
                language = req.get('language', 'english')
                status = req.get('status', 'unknown')
                
                if isinstance(timestamp, str):
                    time_str = timestamp
                else:
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                
                status_icon = "✅" if status == 'success' else "❌"
                stats_text += f"{status_icon} {time_str} - {language.title()}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await update.callback_query.edit_message_text(
            "❌ Error loading statistics",
            parse_mode='Markdown'
        )

async def handle_convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle convert image callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user settings to show current language
    try:
        user = db.get_user(user_id)
        user_settings = user.get('settings', {}) if user else {}
        current_language = user_settings.get('language', 'english')
    except Exception as e:
        current_language = 'english'
    
    language_display = config.LANGUAGE_DISPLAY_NAMES.get(current_language, current_language)
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📸 *Convert Image*\n\n"
        f"Current Language: {language_display}\n\n"
        "Simply send me an image containing text and I'll extract it for you!\n\n"
        "💡 *Tips for best results:*\n"
        "• Use clear, well-lit images\n"
        "• Ensure text is focused\n"
        "• High contrast works best\n"
        "• Choose the right language in settings",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )