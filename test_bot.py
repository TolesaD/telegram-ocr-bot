#!/usr/bin/env python3
"""
Simple Local Test Bot - Minimal dependencies
"""
import os
import logging
import asyncio
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Simple in-memory database
class SimpleDB:
    def __init__(self):
        self.users = {}
        self.requests = []
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def insert_user(self, user_data):
        self.users[user_data['user_id']] = user_data
        return type('Result', (), {'inserted_id': user_data['user_id']})
    
    def update_user_settings(self, user_id, settings):
        if user_id in self.users:
            if 'settings' not in self.users[user_id]:
                self.users[user_id]['settings'] = {}
            self.users[user_id]['settings'].update(settings)
        return type('Result', (), {'matched_count': 1, 'modified_count': 1})
    
    def log_ocr_request(self, request_data):
        self.requests.append(request_data)
        return type('Result', (), {'inserted_id': len(self.requests)})

# Simple text formatter
class SimpleTextFormatter:
    @staticmethod
    def format_text(text, format_type='plain'):
        if format_type == 'markdown':
            # Simple markdown escaping
            for char in ['_', '*', '`', '[']:
                text = text.replace(char, f'\\{char}')
            return text
        elif format_type == 'html':
            return f"<pre>{text}</pre>"
        else:
            return text

# Simple image processor (Tesseract only for now)
class SimpleImageProcessor:
    @staticmethod
    async def extract_text_async(image_bytes, language='eng'):
        try:
            import pytesseract
            from PIL import Image
            import io
            import time
            
            # Simple preprocessing
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Use Tesseract
            text = pytesseract.image_to_string(image, lang=language)
            
            # Clean text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            cleaned_lines = []
            for line in lines:
                if len(line) > 1 and any(c.isalnum() for c in line):
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines) if cleaned_lines else "No readable text found."
            
        except Exception as e:
            return f"Error processing image: {str(e)}"

# Bot handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']
    
    # Save user to database
    user_data = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'settings': {
            'language': 'english',
            'text_format': 'plain'
        }
    }
    db.insert_user(user_data)
    
    welcome_text = (
        f"🎉 Welcome {user.first_name}!\n\n"
        "🤖 *Image-to-Text Converter Bot* (Local Test)\n\n"
        "📸 Send me an image with text, and I'll extract it for you!\n\n"
        "💡 For best results:\n"
        "• Clear, well-lit images\n"
        "• Focused text\n"
        "• High contrast\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Image", callback_data="convert_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    db = context.bot_data['db']
    
    if not message.photo:
        await message.reply_text("❌ Please send an image containing text.")
        return
    
    # Get user settings
    user = db.get_user(user_id)
    language = user.get('settings', {}).get('language', 'english') if user else 'english'
    text_format = user.get('settings', {}).get('text_format', 'plain') if user else 'plain'
    
    # Language mapping
    lang_map = {'english': 'eng', 'spanish': 'spa', 'french': 'fra', 'german': 'deu'}
    lang_code = lang_map.get(language, 'eng')
    
    processing_msg = await message.reply_text("🔄 Processing your image...")
    
    try:
        # Get the best quality photo
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Extract text
        extracted_text = await SimpleImageProcessor.extract_text_async(bytes(photo_bytes), lang_code)
        
        # Format text
        formatted_text = SimpleTextFormatter.format_text(extracted_text, text_format)
        
        # Store for reformatting
        context.user_data['last_extracted_text'] = extracted_text
        
        # Create format buttons
        keyboard = [
            [
                InlineKeyboardButton("📄 Plain", callback_data="reformat_plain"),
                InlineKeyboardButton("📋 Markdown", callback_data="reformat_markdown"),
                InlineKeyboardButton("🌐 HTML", callback_data="reformat_html")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            f"📝 Extracted Text:\n\n{formatted_text}",
            reply_markup=reply_markup,
            parse_mode=None
        )
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error processing image: {str(e)}")

async def handle_reformat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    format_type = query.data.replace('reformat_', '')
    
    if 'last_extracted_text' not in context.user_data:
        await query.edit_message_text("❌ No text available to reformat.")
        return
    
    original_text = context.user_data['last_extracted_text']
    formatted_text = SimpleTextFormatter.format_text(original_text, format_type)
    
    # Create format buttons
    keyboard = [
        [
            InlineKeyboardButton("📄 Plain", callback_data="reformat_plain"),
            InlineKeyboardButton("📋 Markdown", callback_data="reformat_markdown"),
            InlineKeyboardButton("🌐 HTML", callback_data="reformat_html")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    parse_mode = None
    if format_type == 'markdown':
        parse_mode = 'MarkdownV2'
    elif format_type == 'html':
        parse_mode = 'HTML'
    
    try:
        await query.edit_message_text(
            f"📝 Extracted Text ({format_type.upper()}):\n\n{formatted_text}",
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except:
        await query.edit_message_text(
            f"📝 Extracted Text ({format_type.upper()} - plain):\n\n{original_text}",
            reply_markup=reply_markup,
            parse_mode=None
        )

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🌐 Language: English", callback_data="change_language")],
        [InlineKeyboardButton("📝 Format: Plain Text", callback_data="change_format")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ *Settings*\n\n"
        "Configure your preferences:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Image", callback_data="convert_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🤖 *Main Menu*\n\nChoose an option:"
    
    if query:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📸 *Convert Image*\n\n"
        "Send me an image with text, and I'll extract it for you!\n\n"
        "💡 Tips:\n"
        "• Clear, well-lit images\n"
        "• Focused text\n"
        "• High contrast\n"
        "• Straight photos",
        parse_mode='Markdown'
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception: {context.error}")

async def main():
    try:
        logger.info("🤖 Starting Simple Test Bot...")
        
        # Check BOT_TOKEN
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN not found")
            return 1
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Setup simple database
        db = SimpleDB()
        application.bot_data['db'] = db
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.PHOTO, handle_image))
        application.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
        application.add_handler(CallbackQueryHandler(show_settings, pattern="^settings$"))
        application.add_handler(CallbackQueryHandler(handle_convert_image, pattern="^convert_image$"))
        application.add_handler(CallbackQueryHandler(handle_reformat, pattern="^reformat_"))
        application.add_error_handler(error_handler)
        
        logger.info("✅ Handlers registered")
        
        # Start bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("✅ Bot is running! Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        return 1
    finally:
        try:
            if 'application' in locals():
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
        except:
            pass
    
    return 0

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    sys.exit(asyncio.run(main()))