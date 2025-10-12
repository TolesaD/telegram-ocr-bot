from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
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

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = update.callback_query.from_user.id
    
    try:
        stats = db.get_user_stats(user_id)
        
        stats_text = (
            f"📊 *Your Statistics*\n\n"
            f"• Total OCR Requests: {stats['total_requests']}\n"
            f"• Recent Activity: {len(stats['recent_requests'])} requests\n\n"
        )
        
        if stats['recent_requests']:
            stats_text += "📅 Recent requests:\n"
            for req in stats['recent_requests'][:3]:  # Show last 3 requests
                if isinstance(req, dict):
                    timestamp = req.get('timestamp', 'Unknown')
                    language = req.get('language', 'Unknown')
                    # Format timestamp nicely
                    if hasattr(timestamp, 'strftime'):
                        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
                    else:
                        timestamp_str = str(timestamp)
                    stats_text += f"  - {timestamp_str}: {language}\n"
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        stats_text = "📊 *Your Statistics*\n\nNo data available yet."
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        stats_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle convert image button - prompt user to send an image"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📷 *Convert Image to Text*\n\n"
        "Please send me an image containing text and I'll extract it for you!\n\n"
        "💡 *Tips for better results:*\n"
        "• Use good lighting\n"
        "• Ensure text is clear and focused\n"
        "• High contrast works best\n"
        "• Avoid shadows on text",
        parse_mode='Markdown'
    )

# Add handlers for language and format changes
async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu"""
    from utils.image_processing import ImageProcessor
    
    supported_languages = ImageProcessor.get_supported_languages()
    
    keyboard = []
    row = []
    for lang_name in supported_languages.keys():
        row.append(InlineKeyboardButton(lang_name.title(), callback_data=f"set_language_{lang_name}"))
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    if row:  # Add any remaining buttons
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🌐 *Select OCR Language*\n\n"
        "Choose the language for text recognition:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_format_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show text format selection menu"""
    keyboard = [
        [InlineKeyboardButton("📄 Plain Text", callback_data="set_format_plain")],
        [InlineKeyboardButton("📋 Markdown", callback_data="set_format_markdown")],
        [InlineKeyboardButton("🌐 HTML", callback_data="set_format_html")],
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "📝 *Select Text Format*\n\n"
        "Choose how you want the extracted text formatted:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_language_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language change"""
    query = update.callback_query
    await query.answer()
    
    language = query.data.replace('set_language_', '')
    user_id = query.from_user.id
    
    try:
        # Update user settings
        user = db.get_user(user_id)
        if not user:
            user = {'user_id': user_id, 'settings': {}}
        
        user['settings']['language'] = language
        db.update_user_settings(user_id, user['settings'])
        
        await query.edit_message_text(
            f"✅ Language set to: {language.title()}\n\n"
            f"Your OCR will now use {language} for text recognition.",
            parse_mode='Markdown'
        )
        
        # Show settings menu after a delay
        await show_settings_menu(update, context)
        
    except Exception as e:
        print(f"Error updating language: {e}")
        await query.edit_message_text("❌ Error updating language settings.")

async def handle_format_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format change"""
    query = update.callback_query
    await query.answer()
    
    text_format = query.data.replace('set_format_', '')
    user_id = query.from_user.id
    
    try:
        # Update user settings
        user = db.get_user(user_id)
        if not user:
            user = {'user_id': user_id, 'settings': {}}
        
        user['settings']['text_format'] = text_format
        db.update_user_settings(user_id, user['settings'])
        
        await query.edit_message_text(
            f"✅ Text format set to: {text_format.upper()}\n\n"
            f"Your extracted text will now be formatted as {text_format}.",
            parse_mode='Markdown'
        )
        
        # Show settings menu after a delay
        await show_settings_menu(update, context)
        
    except Exception as e:
        print(f"Error updating format: {e}")
        await query.edit_message_text("❌ Error updating format settings.")