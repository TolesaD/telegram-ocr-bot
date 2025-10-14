from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import traceback
from utils.image_processing import ocr_processor
from utils.text_formatter import TextFormatter
import config
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

# Processing cache to prevent multiple concurrent requests
processing_cache = {}

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming images with multi-language support"""
    # Get database from bot_data
    db = context.bot_data.get('db')
    
    user_id = update.effective_user.id
    message = update.message
    
    if not message.photo:
        await message.reply_text("❌ Please send an image containing text.")
        return
    
    # Prevent multiple concurrent processing
    if user_id in processing_cache:
        await message.reply_text("⏳ Please wait for your current image to finish processing.")
        return
    
    # Get user settings
    try:
        user = db.get_user(user_id) if db else None
        user_settings = user.get('settings', {}) if user else {}
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        user_settings = {}
    
    language = user_settings.get('language', 'english')
    text_format = user_settings.get('text_format', 'plain')
    
    # Get language code
    lang_code = config.SUPPORTED_LANGUAGES.get(language, 'eng')
    language_display = config.LANGUAGE_DISPLAY_NAMES.get(language, language)
    
    # Get the best quality photo
    photo = message.photo[-1]
    
    # Mark as processing
    processing_cache[user_id] = True
    processing_msg = None
    
    try:
        processing_msg = await message.reply_text(f"🔄 Processing your image ({language_display})...")
        start_time = time.time()
        
        # Download image
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Validate size
        if len(photo_bytes) > config.MAX_IMAGE_SIZE:
            await processing_msg.edit_text("❌ Image is too large. Please send an image smaller than 8MB.")
            return
        
        # Update status
        await processing_msg.edit_text(f"🔄 Processing image in {language_display}...")
        
        # Extract text with timeout
        try:
            extracted_text = await asyncio.wait_for(
                ocr_processor.extract_text_optimized(bytes(photo_bytes), language),
                timeout=config.PROCESSING_TIMEOUT
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Processed image for user {user_id} in {processing_time:.2f}s (Language: {language})")
            
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                f"⏰ Processing took too long for {language_display}. Please try:\n"
                "• A smaller image\n" 
                "• Cropping to text area\n"
                "• Better lighting\n"
                "• Less complex background"
            )
            return
        
        if not extracted_text or "No readable text" in extracted_text:
            await processing_msg.edit_text(
                f"❌ No readable text found in {language_display}.\n\n"
                "💡 *Tips for better results:*\n"
                "• Use good lighting\n"
                "• Ensure text is clear and focused\n"
                "• Choose the right language in settings\n"
                "• High contrast works best\n"
                "• Take straight photos",
                parse_mode='Markdown'
            )
            return
        
        # Store the original extracted text in context for reformatting
        context.user_data[f'original_text_{message.message_id}'] = extracted_text
        
        # Format text
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # Log successful request
        try:
            if db:
                db.log_ocr_request({
                    'user_id': user_id,
                    'timestamp': datetime.now(),
                    'language': language,
                    'language_display': language_display,
                    'format': text_format,
                    'text_length': len(extracted_text),
                    'processing_time': processing_time,
                    'status': 'success'
                })
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
        
        # Prepare response - USE PLAIN TEXT FORMATTING FIRST
        response_text = f"📝 Extracted Text ({language_display}, {text_format.upper()}):\n\n{formatted_text}"
        
        # Add format options
        keyboard = [
            [
                InlineKeyboardButton("📄 Plain", callback_data=f"reformat_plain_{message.message_id}"),
                InlineKeyboardButton("📋 Markdown", callback_data=f"reformat_markdown_{message.message_id}"),
                InlineKeyboardButton("🌐 HTML", callback_data=f"reformat_html_{message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode=None  # Start with plain text to ensure it works
        )
        
        logger.info(f"✅ Successfully processed image for user {user_id} in {language}")
        
    except asyncio.TimeoutError:
        error_msg = (
            f"⏰ Processing timeout for {language_display}. Please try:\n\n"
            "• A smaller image\n"
            "• Cropping to text area\n" 
            "• Better lighting\n"
            "• Clearer text\n"
            "• Try a different language"
        )
        if processing_msg:
            await processing_msg.edit_text(error_msg)
        else:
            await message.reply_text(error_msg)
            
    except Exception as e:
        error_msg = await handle_ocr_error(e, language_display)
        if processing_msg:
            await processing_msg.edit_text(error_msg)
        else:
            await message.reply_text(error_msg)
        
        # Log error
        try:
            if db:
                db.log_ocr_request({
                    'user_id': user_id,
                    'timestamp': datetime.now(),
                    'language': language,
                    'language_display': language_display,
                    'format': text_format,
                    'status': 'error',
                    'error': str(e)
                })
        except Exception as log_error:
            logger.error(f"Error logging OCR error: {log_error}")
    
    finally:
        # Remove from processing cache
        processing_cache.pop(user_id, None)

async def handle_ocr_error(error, language_display):
    """Handle OCR errors with user-friendly messages"""
    error_str = str(error)
    logger.error(f"OCR Error for {language_display}: {error_str}")
    
    if "timeout" in error_str.lower():
        return (
            f"⏰ Processing timeout for {language_display}. Please try:\n\n"
            "• Smaller image (under 5MB)\n"
            "• Better lighting and focus\n"
            "• High contrast text\n"
            "• Crop to text area\n"
            "• Try a different language"
        )
    elif "no readable text" in error_str.lower():
        return (
            f"❌ No readable text found in {language_display}.\n\n"
            "💡 *Tips:*\n"
            "• Use good, even lighting\n"
            "• Ensure text is clear and not blurry\n"
            "• Choose the correct language\n"
            "• Use high contrast\n"
            "• Take straight, focused photos"
        )
    elif "language" in error_str.lower() and "not installed" in error_str.lower():
        return f"❌ {language_display} language pack not installed. Please try English or another supported language."
    elif "tesseract" in error_str.lower() and "not configured" in error_str.lower():
        return "❌ OCR engine is not available. Please contact administrator."
    else:
        return f"❌ Error processing image in {language_display}: {error_str}"

async def handle_reformat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text reformatting - ULTRA SIMPLE VERSION"""
    query = update.callback_query
    await query.answer()
    
    # Get database from bot_data
    db = context.bot_data.get('db')
    
    try:
        data = query.data
        parts = data.split('_')
        format_type = parts[1]
        original_message_id = int(parts[2])
        
        logger.info(f"🔄 Reformatting to {format_type} for message {original_message_id}")
        
        # Get the original text from context
        original_text_key = f'original_text_{original_message_id}'
        
        if original_text_key not in context.user_data:
            await query.edit_message_text("❌ Original text not found. Please process the image again.")
            return
        
        original_text = context.user_data[original_text_key]
        
        if not original_text or len(original_text.strip()) < 2:
            await query.edit_message_text("❌ No text available to reformat.")
            return
        
        # Reformat text - use the simple formatter
        formatted_text = TextFormatter.format_text(original_text, format_type)
        
        # Prepare response - ALWAYS use plain text first
        response_text = f"📝 Extracted Text ({format_type.upper()}):\n\n{formatted_text}"
        
        # Only set parse_mode for formats that support it
        parse_mode = None
        if format_type == 'markdown':
            # Try to use Markdown, but if it fails, fallback to plain
            try:
                # Test if the text can be parsed as Markdown
                test_text = TextFormatter.format_markdown_simple("test")
                if test_text:
                    parse_mode = 'MarkdownV2'
            except:
                parse_mode = None
        elif format_type == 'html':
            parse_mode = 'HTML'
        
        # Create new keyboard
        keyboard = [
            [
                InlineKeyboardButton("📄 Plain", callback_data=f"reformat_plain_{original_message_id}"),
                InlineKeyboardButton("📋 Markdown", callback_data=f"reformat_markdown_{original_message_id}"),
                InlineKeyboardButton("🌐 HTML", callback_data=f"reformat_html_{original_message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Try to send with formatting, fallback to plain text if it fails
        try:
            await query.edit_message_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"✅ Successfully reformatted to {format_type}")
        except Exception as format_error:
            logger.warning(f"Formatting failed, using plain text: {format_error}")
            await query.edit_message_text(
                f"📝 Extracted Text ({format_type.upper()} - showing as plain text):\n\n{original_text}",
                reply_markup=reply_markup,
                parse_mode=None
            )
        
    except Exception as e:
        logger.error(f"❌ Error in reformat: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Ultimate fallback
        try:
            original_text = context.user_data.get(f'original_text_{original_message_id}', 'No text available')
            await query.edit_message_text(
                f"❌ Error reformatting text. Showing in plain format:\n\n{original_text}",
                parse_mode=None
            )
        except:
            await query.edit_message_text("❌ Error reformatting text. Please process the image again.")