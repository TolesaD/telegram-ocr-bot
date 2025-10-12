from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import io
import traceback
from database.mongodb import db
from utils.image_processing import ImageProcessor
from utils.text_formatter import TextFormatter
import config  # Import config directly
import logging

logger = logging.getLogger(__name__)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming images"""
    user_id = update.effective_user.id
    message = update.message
    
    # Check if message contains photo
    if not message.photo:
        await message.reply_text("❌ Please send an image containing text.")
        return
    
    # Get user settings with error handling
    try:
        user = db.get_user(user_id)
        if user and 'settings' in user:
            user_settings = user['settings']
        else:
            user_settings = {}
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        user_settings = {}
    
    language = user_settings.get('language', 'english')
    text_format = user_settings.get('text_format', 'plain')
    
    # Get the highest quality photo
    photo = message.photo[-1]
    
    # Show processing message
    processing_msg = await message.reply_text("🔄 Processing your image...")
    
    try:
        # Download image
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        logger.info(f"📸 Image downloaded: {len(photo_bytes)} bytes")
        
        # Validate image size
        if len(photo_bytes) > 10 * 1024 * 1024:  # 10MB limit
            await processing_msg.edit_text("❌ Image is too large. Please send an image smaller than 10MB.")
            return
        
        # Get language code - FIXED: Use config directly instead of config.Config
        lang_code = config.SUPPORTED_LANGUAGES.get(language, 'eng')
        
        # Update processing message
        await processing_msg.edit_text(f"🔄 Processing image with {language} OCR...")
        
        # Extract text
        extracted_text = ImageProcessor.extract_text(bytes(photo_bytes), lang_code)
        
        if not extracted_text or "No readable text" in extracted_text:
            await processing_msg.edit_text(
                "❌ No readable text found in the image.\n\n"
                "💡 Tips for better results:\n"
                "• Use good lighting\n"
                "• Ensure text is clear and not blurry\n"
                "• Avoid shadows on the text\n"
                "• Use high contrast (black text on white background)\n"
                "• Take a straight, focused photo"
            )
            return
        
        # Format text
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # Log the request (with error handling)
        try:
            db.log_ocr_request({
                'user_id': user_id,
                'timestamp': datetime.now(),
                'language': language,
                'format': text_format,
                'text_length': len(extracted_text)
            })
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
        
        # Prepare response
        if text_format == 'markdown':
            parse_mode = 'MarkdownV2'
        elif text_format == 'html':
            parse_mode = 'HTML'
        else:
            parse_mode = None
        
        # Truncate very long text to avoid Telegram message limits
        if len(formatted_text) > 4000:
            formatted_text = formatted_text[:4000] + "\n\n... (text truncated due to length)"
        
        # Send extracted text
        response_text = f"📝 *Extracted Text* \\({text_format.upper()}\\):\n\n{formatted_text}"
        
        # Add format options keyboard
        keyboard = [
            [
                InlineKeyboardButton("📄 Plain Text", callback_data=f"reformat_plain_{message.message_id}"),
                InlineKeyboardButton("📋 Markdown", callback_data=f"reformat_markdown_{message.message_id}"),
                InlineKeyboardButton("🌐 HTML", callback_data=f"reformat_html_{message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode=parse_mode if text_format != 'plain' else None
        )
        
        logger.info(f"✅ Successfully processed image for user {user_id}")
        
    except Exception as e:
        error_detail = str(e)
        logger.error(f"OCR Error: {error_detail}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # User-friendly error messages
        if "Tesseract not configured" in error_detail:
            error_message = "❌ OCR engine is not available. Please contact the administrator."
        elif "Language" in error_detail and "not installed" in error_detail:
            error_message = f"❌ {error_detail}. Please try English or change language in settings."
        elif "No readable text" in error_detail:
            error_message = (
                "❌ No readable text found.\n\n"
                "💡 Try:\n"
                "• Better lighting\n"
                "• Higher contrast\n"
                "• Clearer text\n"
                "• Less background noise"
            )
        elif "image file is truncated" in error_detail or "cannot identify image file" in error_detail:
            error_message = "❌ Invalid image format. Please send a valid JPEG, PNG, or WebP image."
        else:
            error_message = f"❌ Error processing image: {error_detail}"
        
        await processing_msg.edit_text(error_message)

async def handle_reformat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text reformatting"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    format_type = data.split('_')[1]  # plain, markdown, or html
    original_message_id = int(data.split('_')[2])
    
    # Get original message text
    original_text = query.message.text
    
    # Remove the format prefix if present
    if "Extracted Text" in original_text:
        text_only = original_text.split("\n\n", 1)[1]
    else:
        text_only = original_text
    
    # Reformat text
    formatted_text = TextFormatter.format_text(text_only, format_type)
    
    # Prepare response
    if format_type == 'markdown':
        parse_mode = 'MarkdownV2'
    elif format_type == 'html':
        parse_mode = 'HTML'
    else:
        parse_mode = None
    
    response_text = f"📝 *Extracted Text* \\({format_type.upper()}\\):\n\n{formatted_text}"
    
    # Update message
    await query.edit_message_text(
        response_text,
        parse_mode=parse_mode if format_type != 'plain' else None
    )