# handlers/ocr.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import traceback
from utils.image_processing import ocr_processor, performance_monitor
from utils.text_formatter import TextFormatter
import config
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

# Enhanced processing cache with timeout
processing_cache = {}
CACHE_TIMEOUT = 30  # seconds

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced image handler with performance optimizations"""
    db = context.bot_data.get('db')
    user_id = update.effective_user.id
    message = update.message
    
    if not message.photo:
        await message.reply_text("❌ Please send an image containing text.")
        return
    
    # Enhanced concurrent processing prevention
    current_time = time.time()
    if user_id in processing_cache:
        cache_time = processing_cache[user_id]['timestamp']
        if current_time - cache_time < CACHE_TIMEOUT:
            await message.reply_text("⏳ Please wait for your current image to finish processing.")
            return
        else:
            # Remove expired cache entry
            processing_cache.pop(user_id, None)
    
    # Get user settings (no language, only format)
    try:
        user = db.get_user(user_id) if db else None
        user_settings = user.get('settings', {}) if user else {}
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        user_settings = {}
    
    text_format = user_settings.get('text_format', 'plain')
    
    # No language selection - auto detection handled in OCR
    
    # Mark as processing with enhanced tracking
    processing_cache[user_id] = {
        'timestamp': current_time,
        'message_id': message.message_id
    }
    
    processing_msg = None
    
    try:
        processing_msg = await message.reply_text(
            f"🔄 Processing your image...\n"
            f"⚡ Using enhanced OCR engine"
        )
        start_time = time.time()
        
        # Download image with timeout
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await asyncio.wait_for(
            photo_file.download_as_bytearray(),
            timeout=15.0
        )
        
        # Validate size
        if len(photo_bytes) > config.MAX_IMAGE_SIZE:
            await processing_msg.edit_text("❌ Image is too large. Please send an image smaller than 20MB.")
            return
        
        # Update status with language detection info
        await processing_msg.edit_text(f"🔍 Analyzing image content...\n⚡ Detecting text language")
        
        # Extract text with enhanced timeout
        try:
            extracted_text = await asyncio.wait_for(
                ocr_processor.extract_text_optimized(bytes(photo_bytes)),
                timeout=config.PROCESSING_TIMEOUT
            )
            
            processing_time = time.time() - start_time
            performance_monitor.record_request(processing_time)
            
            logger.info(f"✅ Processed image for user {user_id} in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                f"⏰ Processing took too long.\n\n"
                "💡 *Optimization Tips:*\n"
                "• Use smaller, focused images\n"
                "• Crop to text area only\n"
                "• Better lighting and contrast\n"
                "• Clear, non-blurry text",
                parse_mode='Markdown'
            )
            return
        
        # Enhanced text validation
        if not extracted_text or len(extracted_text.strip()) < 5:
            await processing_msg.edit_text(
                f"❌ No readable text found or text too short.\n\n"
                "🎯 *For Better Results:*\n"
                "• Use high-contrast images\n"
                "• Ensure text is horizontal\n"
                "• Good, even lighting\n"
                "• Clear, focused text\n"
                "• Avoid blurry or distorted images",
                parse_mode='Markdown'
            )
            return
        
        # Store the original extracted text
        context.user_data[f'original_text_{message.message_id}'] = extracted_text
        
        # Format text
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # Log successful request
        try:
            if db:
                db.log_ocr_request({
                    'user_id': user_id,
                    'timestamp': datetime.now(),
                    'format': text_format,
                    'text_length': len(extracted_text),
                    'processing_time': processing_time,
                    'status': 'success'
                })
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
        
        # Enhanced response with performance info
        text_preview = extracted_text[:100] + "..." if len(extracted_text) > 100 else extracted_text
        
        if text_format == 'html':
            response_text = (
                f"📝 **Extracted Text** (HTML Format - Copy Friendly)\n"
                f"⏱️ Processed in: {processing_time:.2f}s\n"
                f"📊 Characters: {len(extracted_text)}\n\n"
                f"{formatted_text}"
            )
            parse_mode = 'HTML'
        else:
            response_text = (
                f"📝 **Extracted Text** (Plain Format)\n"
                f"⏱️ Processed in: {processing_time:.2f}s\n"
                f"📊 Characters: {len(extracted_text)}\n\n"
                f"{formatted_text}"
            )
            parse_mode = None
        
        # Handle long messages
        messages = TextFormatter.split_long_message(response_text)
        
        # Enhanced format options
        keyboard = [
            [
                InlineKeyboardButton("📄 Plain Text", callback_data=f"reformat_plain_{message.message_id}"),
                InlineKeyboardButton("📋 Copy HTML", callback_data=f"reformat_html_{message.message_id}")
            ],
            [
                InlineKeyboardButton("🔄 Process Again", callback_data="convert_image")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if len(messages) > 1:
            # Send first part with buttons
            await processing_msg.edit_text(
                messages[0],
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            # Send remaining parts
            for msg in messages[1:]:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=msg,
                    parse_mode=parse_mode
                )
        else:
            await processing_msg.edit_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        
        logger.info(f"✅ Successfully processed image for user {user_id}")
        
    except asyncio.TimeoutError:
        error_msg = (
            f"⏰ Processing timeout.\n\n"
            "🚀 *Quick Fixes:*\n"
            "• Smaller images work faster\n"
            "• Crop to text area\n"
            "• Better image quality\n"
            "• Check image size"
        )
        if processing_msg:
            await processing_msg.edit_text(error_msg, parse_mode='Markdown')
        else:
            await message.reply_text(error_msg, parse_mode='Markdown')
            
    except Exception as e:
        error_msg = await handle_ocr_error(e)
        if processing_msg:
            await processing_msg.edit_text(error_msg, parse_mode='Markdown')
        else:
            await message.reply_text(error_msg, parse_mode='Markdown')
        
        # Log error
        try:
            if db:
                db.log_ocr_request({
                    'user_id': user_id,
                    'timestamp': datetime.now(),
                    'format': text_format,
                    'status': 'error',
                    'error': str(e)
                })
        except Exception as log_error:
            logger.error(f"Error logging OCR error: {log_error}")
    
    finally:
        # Remove from processing cache
        processing_cache.pop(user_id, None)

async def handle_ocr_error(error):
    """Enhanced error handling with better user guidance"""
    error_str = str(error)
    logger.error(f"OCR Error: {error_str}")
    
    if "timeout" in error_str.lower():
        return (
            f"⏰ Processing timeout.\n\n"
            "⚡ *Performance Tips:*\n"
            "• Images under 5MB work best\n"
            "• Crop to essential text area\n"
            "• High contrast improves speed\n"
            "• Clear, focused images"
        )
    elif "no readable text" in error_str.lower() or "very little text" in error_str.lower():
        return (
            f"🔍 No readable text found.\n\n"
            "🎯 *Quality Tips:*\n"
            "• Ensure text is clear and focused\n"
            "• Good lighting reduces errors\n"
            "• High contrast backgrounds\n"
            "• Straight, horizontal text\n"
            "• Avoid blurry or distorted images"
        )
    elif "language" in error_str.lower() and "not installed" in error_str.lower():
        return f"❌ Language pack not available. Please try English or another supported language."
    else:
        return (
            f"❌ Error processing image.\n\n"
            "💡 *Try This:*\n"
            "• Send a different image\n"
            "• Check image quality\n"
            "• Ensure text is readable\n"
            "• Try cropping the image"
        )

async def handle_reformat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced reformatting with better error handling"""
    query = update.callback_query
    await query.answer()
    
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
        
        # Enhanced reformatting
        formatted_text = TextFormatter.format_text(original_text, format_type)
        
        # Enhanced response
        if format_type == 'html':
            response_text = f"📝 **Reformatted Text** ({format_type.upper()} - Copy Friendly)\n\n{formatted_text}"
            parse_mode = 'HTML'
        else:
            response_text = f"📝 **Reformatted Text** ({format_type.upper()})\n\n{formatted_text}"
            parse_mode = None
        
        # Enhanced keyboard
        other_format = 'html' if format_type == 'plain' else 'plain'
        keyboard = [
            [
                InlineKeyboardButton(f"📄 {other_format.upper()}", callback_data=f"reformat_{other_format}_{original_message_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enhanced error handling for formatting
        try:
            await query.edit_message_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"✅ Successfully reformatted to {format_type}")
        except Exception as format_error:
            logger.warning(f"Formatting failed, using plain text: {format_error}")
            # Use plain text without parse_mode
            await query.edit_message_text(
                f"📝 **Extracted Text** ({format_type.upper()} - plain version)\n\n{original_text}",
                reply_markup=reply_markup,
                parse_mode=None
            )
        
    except Exception as e:
        logger.error(f"❌ Error in reformat: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Ultimate fallback - show original text
        try:
            original_text = context.user_data.get(f'original_text_{original_message_id}', 'No text available')
            await query.edit_message_text(
                f"❌ Error reformatting text. Showing original:\n\n{original_text}",
                parse_mode=None
            )
        except Exception as final_error:
            logger.error(f"Final fallback failed: {final_error}")
            await query.edit_message_text("❌ Error reformatting text. Please process the image again.")

async def handle_convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle convert image callback"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("📸 Please send an image containing text to convert.")

# OCR callback handler
async def handle_ocr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OCR-related callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("reformat_"):
        await handle_reformat(update, context)
    elif query.data == "convert_image":
        await handle_convert_image(update, context)