from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import traceback
from database.mongodb import db
from utils.image_processing import ImageProcessor
from utils.text_formatter import TextFormatter
import config
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming images with timeout protection"""
    user_id = update.effective_user.id
    message = update.message
    
    if not message.photo:
        await message.reply_text("❌ Please send an image containing text.")
        return
    
    # Get user settings
    try:
        user = db.get_user(user_id)
        user_settings = user.get('settings', {}) if user else {}
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        user_settings = {}
    
    language = user_settings.get('language', 'english')
    text_format = user_settings.get('text_format', 'plain')
    
    photo = message.photo[-1]
    processing_msg = await message.reply_text("🔄 Processing your image... This may take a moment.")
    
    try:
        # Download image with timeout
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        logger.info(f"📸 Processing image for user {user_id}")
        
        # Validate size
        if len(photo_bytes) > 5 * 1024 * 1024:  # Reduced to 5MB for faster processing
            await processing_msg.edit_text("❌ Image is too large. Please send an image smaller than 5MB.")
            return
        
        # Get language code
        lang_code = config.SUPPORTED_LANGUAGES.get(language, 'eng')
        
        # Update processing message
        await processing_msg.edit_text(f"🔄 Processing image ({language})...")
        
        # Extract text with timeout protection
        try:
            # Set a timeout for OCR processing (30 seconds)
            extracted_text = await asyncio.wait_for(
                ImageProcessor.extract_text_async(bytes(photo_bytes), lang_code),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                "⏰ Processing took too long. The image might be too complex.\n\n"
                "💡 Try:\n"
                "• Cropping to just the text area\n"
                "• Using a smaller image\n"
                "• Ensuring text is clear and focused"
            )
            return
        
        if not extracted_text or "No readable text" in extracted_text:
            await processing_msg.edit_text(
                "❌ No readable text found in the image.\n\n"
                "💡 *Tips for better results:*\n"
                "• Use good, even lighting\n"
                "• Ensure text is clear and not blurry\n"
                "• Avoid shadows on the text\n"
                "• Use high contrast (black text on white background)\n"
                "• Take a straight, focused photo\n"
                "• Try cropping to just the text area",
                parse_mode='Markdown'
            )
            return
        
        # Format text
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # Log the request
        try:
            db.log_ocr_request({
                'user_id': user_id,
                'timestamp': datetime.now(),
                'language': language,
                'format': text_format,
                'text_length': len(extracted_text),
                'status': 'success'
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
        
        # Truncate if too long
        if len(formatted_text) > 4000:
            formatted_text = formatted_text[:4000] + "\n\n... (text truncated due to length)"
        
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
        
    except asyncio.TimeoutError:
        await processing_msg.edit_text(
            "⏰ Processing timeout. The image might be too large or complex.\n\n"
            "💡 Try sending a smaller image or cropping to just the text."
        )
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
        elif "Timed out" in error_detail or "timeout" in error_detail.lower():
            error_message = (
                "⏰ Processing timeout.\n\n"
                "💡 Try:\n"
                "• Sending a smaller image\n"
                "• Cropping to just the text\n"
                "• Using better lighting\n"
                "• Less complex images"
            )
        else:
            error_message = f"❌ Error processing image: {error_detail}"
        
        await processing_msg.edit_text(error_message)

async def handle_reformat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text reformatting"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    format_type = data.split('_')[1]
    original_message_id = int(data.split('_')[2])
    
    original_text = query.message.text
    
    if "Extracted Text" in original_text:
        text_only = original_text.split("\n\n", 1)[1]
    else:
        text_only = original_text
    
    formatted_text = TextFormatter.format_text(text_only, format_type)
    
    if format_type == 'markdown':
        parse_mode = 'MarkdownV2'
    elif format_type == 'html':
        parse_mode = 'HTML'
    else:
        parse_mode = None
    
    response_text = f"📝 *Extracted Text* \\({format_type.upper()}\\):\n\n{formatted_text}"
    
    await query.edit_message_text(
        response_text,
        parse_mode=parse_mode if format_type != 'plain' else None
    )