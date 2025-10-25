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
    """Production-grade image handler with enhanced performance and reliability"""
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
    
    # Get user settings
    try:
        user = db.get_user(user_id) if db else None
        user_settings = user.get('settings', {}) if user else {}
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        user_settings = {}
    
    text_format = user_settings.get('text_format', 'plain')
    
    # Mark as processing with enhanced tracking
    processing_cache[user_id] = {
        'timestamp': current_time,
        'message_id': message.message_id
    }
    
    processing_msg = None
    
    try:
        # Send initial processing message
        processing_msg = await message.reply_text(
            "🔄 *Production OCR Processing Started*\n\n"
            "⚡ Using advanced AI-powered text extraction\n"
            "🎯 Optimized for accuracy and speed\n"
            "⏰ Estimated time: 2-8 seconds",
            parse_mode='Markdown'
        )
        
        start_time = time.time()
        
        # Download image with timeout
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        
        # Show download progress
        await processing_msg.edit_text(
            "📥 *Downloading Image*\n\n"
            "⚡ Optimizing for OCR processing...",
            parse_mode='Markdown'
        )
        
        photo_bytes = await asyncio.wait_for(
            photo_file.download_as_bytearray(),
            timeout=20.0
        )
        
        # Validate size
        if len(photo_bytes) > config.MAX_IMAGE_SIZE:
            await processing_msg.edit_text(
                "❌ *Image Too Large*\n\n"
                "Please send an image smaller than 20MB.\n"
                "💡 Tip: Compress or crop the image first.",
                parse_mode='Markdown'
            )
            return
        
        # Show processing status
        await processing_msg.edit_text(
            "🔍 *Advanced Text Extraction*\n\n"
            "• Preprocessing image for optimal quality\n"
            "• Analyzing text structure and layout\n"
            "• Applying multi-language recognition\n"
            "• Ensuring formatting preservation\n\n"
            "⏳ This may take a few seconds...",
            parse_mode='Markdown'
        )
        
        # Extract text with production-grade timeout
        try:
            extracted_text = await asyncio.wait_for(
                ocr_processor.extract_text_optimized(bytes(photo_bytes)),
                timeout=20  # Increased for production processing
            )
            
            processing_time = time.time() - start_time
            performance_monitor.record_request(processing_time)
            
            logger.info(f"✅ Production OCR completed for user {user_id} in {processing_time:.2f}s")
            
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                "⏰ *Processing Timeout*\n\n"
                "The image took too long to process.\n\n"
                "🚀 *Quick Solutions:*\n"
                "• Use smaller images (under 2MB)\n"
                "• Crop to text area only\n"
                "• Better lighting and contrast\n"
                "• Clear, non-blurry text\n\n"
                "🔄 Please try again with an optimized image.",
                parse_mode='Markdown'
            )
            return
        
        # Handle OCR results
        if not extracted_text or any(phrase in extracted_text for phrase in [
            "No readable text", "Error processing", "Processing timeout", "System error"
        ]):
            await processing_msg.edit_text(
                extracted_text if extracted_text else "No readable text found in the image.",
                parse_mode='Markdown'
            )
            return
        
        # Store the original extracted text
        context.user_data[f'original_text_{message.message_id}'] = extracted_text
        
        # Format text based on user preference
        formatted_text = TextFormatter.format_text(extracted_text, text_format)
        
        # Log successful request to database
        try:
            if db:
                db.log_ocr_request({
                    'user_id': user_id,
                    'timestamp': datetime.now(),
                    'format': text_format,
                    'text_length': len(extracted_text),
                    'processing_time': processing_time,
                    'status': 'success',
                    'confidence': getattr(performance_monitor, 'last_confidence', 0)
                })
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
        
        # Enhanced response with performance info
        performance_stats = performance_monitor.get_stats()
        
        if text_format == 'html':
            response_text = (
                f"✅ **Text Extraction Complete**\n\n"
                f"📊 *Performance Metrics:*\n"
                f"• ⏱️ Processing Time: {processing_time:.2f}s\n"
                f"• 📈 System Accuracy: {performance_stats.get('avg_confidence', 0):.1f}%\n"
                f"• 🎯 Success Rate: {performance_stats.get('success_rate', 0):.1f}%\n\n"
                f"📝 **Extracted Content (HTML Format):**\n\n"
                f"{formatted_text}"
            )
            parse_mode = 'HTML'
        else:
            response_text = (
                f"✅ **Text Extraction Complete**\n\n"
                f"📊 *Performance Metrics:*\n"
                f"• ⏱️ Processing Time: {processing_time:.2f}s\n"
                f"• 📈 System Accuracy: {performance_stats.get('avg_confidence', 0):.1f}%\n"
                f"• 🎯 Success Rate: {performance_stats.get('success_rate', 0):.1f}%\n\n"
                f"📝 **Extracted Content:**\n\n"
                f"{formatted_text}"
            )
            parse_mode = 'Markdown'
        
        # Handle long messages with smart splitting
        messages = TextFormatter.split_long_message(response_text)
        
        # Enhanced format options with better UX
        keyboard = [
            [
                InlineKeyboardButton("📄 Plain Text", callback_data=f"reformat_plain_{message.message_id}"),
                InlineKeyboardButton("📋 HTML Format", callback_data=f"reformat_html_{message.message_id}")
            ],
            [
                InlineKeyboardButton("🔄 Process Another", callback_data="convert_image"),
                InlineKeyboardButton("📊 View Stats", callback_data="statistics")
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
            # Send remaining parts without buttons
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
        
        logger.info(f"✅ Successfully processed image for user {user_id} - Text length: {len(extracted_text)} chars")
        
    except asyncio.TimeoutError:
        error_msg = (
            "⏰ *Processing Timeout*\n\n"
            "The operation took longer than expected.\n\n"
            "⚡ *Performance Tips:*\n"
            "• Images under 5MB process faster\n"
            "• Crop to essential text areas\n"
            "• High contrast improves speed\n"
            "• Clear, focused images work best\n\n"
            "🔄 Please try again with an optimized image."
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
        
        # Log error to database
        try:
            if db:
                db.log_ocr_request({
                    'user_id': user_id,
                    'timestamp': datetime.now(),
                    'format': text_format,
                    'status': 'error',
                    'error': str(e),
                    'processing_time': time.time() - start_time if 'start_time' in locals() else 0
                })
        except Exception as log_error:
            logger.error(f"Error logging OCR error: {log_error}")
    
    finally:
        # Always remove from processing cache
        processing_cache.pop(user_id, None)

async def handle_ocr_error(error):
    """Enhanced error handling with production-grade user guidance"""
    error_str = str(error)
    logger.error(f"Production OCR Error: {error_str}")
    
    if "timeout" in error_str.lower():
        return (
            "⏰ *Processing Timeout*\n\n"
            "The system took too long to process your image.\n\n"
            "🚀 *Immediate Solutions:*\n"
            "• Use images under 2MB\n"
            "• Crop to text area only\n"
            "• Better lighting conditions\n"
            "• Higher contrast images\n\n"
            "🔄 Please try again with an optimized image."
        )
    elif "no readable text" in error_str.lower():
        return (
            "🔍 *Text Detection Failed*\n\n"
            "The system couldn't find readable text in your image.\n\n"
            "🎯 *Quality Guidelines:*\n"
            "• Ensure text is clear and focused\n"
            "• Good lighting reduces errors\n"
            "• High contrast backgrounds\n"
            "• Straight, horizontal text\n"
            "• Avoid heavy compression\n\n"
            "📸 *Optimal Image Types:*\n"
            "• Documents and printed text\n"
            "• High-quality screenshots\n"
            "• Well-lit signs or menus"
        )
    elif "language" in error_str.lower() and "not installed" in error_str.lower():
        return (
            "🌍 *Language Support*\n\n"
            "The requested language pack is not available.\n\n"
            "✅ *Supported Languages:*\n"
            "• English (Primary)\n"
            "• Amharic\n"
            "• Chinese, Japanese, Korean\n"
            "• Arabic, Russian, Spanish\n"
            "• French, German, and more\n\n"
            "The system automatically detects the language."
        )
    elif "memory" in error_str.lower() or "size" in error_str.lower():
        return (
            "💾 *System Resources*\n\n"
            "The image is too large for processing.\n\n"
            "📏 *Size Limits:*\n"
            "• Maximum size: 20MB\n"
            "• Optimal size: Under 5MB\n"
            "• Best performance: Under 2MB\n\n"
            "💡 Please compress or crop your image."
        )
    else:
        return (
            "❌ *System Error*\n\n"
            "An unexpected error occurred during processing.\n\n"
            "🔄 *Troubleshooting Steps:*\n"
            "1. Try a different image\n"
            "2. Check image quality and size\n"
            "3. Ensure good lighting\n"
            "4. Wait a moment and retry\n\n"
            "⚡ The system will automatically recover."
        )

async def handle_reformat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced reformatting with production-grade error handling"""
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data.get('db')
    
    try:
        data = query.data
        parts = data.split('_')
        format_type = parts[1]
        original_message_id = int(parts[2])
        
        logger.info(f"🔄 Reformatting to {format_type} for message {original_message_id}")
        
        # Show reformatting status
        await query.edit_message_text(
            f"🔄 Reformatting to {format_type.upper()}...",
            parse_mode='Markdown'
        )
        
        # Get the original text from context
        original_text_key = f'original_text_{original_message_id}'
        
        if original_text_key not in context.user_data:
            await query.edit_message_text(
                "❌ *Original Text Not Found*\n\n"
                "The original text is no longer available.\n"
                "Please process the image again.",
                parse_mode='Markdown'
            )
            return
        
        original_text = context.user_data[original_text_key]
        
        if not original_text or len(original_text.strip()) < 2:
            await query.edit_message_text(
                "❌ *No Text Available*\n\n"
                "No text is available for reformatting.\n"
                "Please process a new image.",
                parse_mode='Markdown'
            )
            return
        
        # Enhanced reformatting with error handling
        try:
            formatted_text = TextFormatter.format_text(original_text, format_type)
            
            if not formatted_text:
                raise ValueError("Formatted text is empty")
                
        except Exception as format_error:
            logger.warning(f"Formatting failed, using plain text: {format_error}")
            formatted_text = original_text
            format_type = 'plain'  # Fallback to plain text
        
        # Enhanced response based on format type
        if format_type == 'html':
            response_text = (
                f"📋 **Reformatted Text** (HTML Format - Copy Friendly)\n\n"
                f"💡 *Easy to copy and paste into documents*\n\n"
                f"{formatted_text}"
            )
            parse_mode = 'HTML'
        else:
            response_text = (
                f"📄 **Reformatted Text** (Plain Format)\n\n"
                f"💡 *Clean and readable text format*\n\n"
                f"{formatted_text}"
            )
            parse_mode = 'Markdown'
        
        # Enhanced keyboard with better UX
        other_format = 'html' if format_type == 'plain' else 'plain'
        other_format_name = 'HTML Format' if format_type == 'plain' else 'Plain Text'
        
        keyboard = [
            [
                InlineKeyboardButton(f"🔄 {other_format_name}", callback_data=f"reformat_{other_format}_{original_message_id}"),
                InlineKeyboardButton("📸 New Image", callback_data="convert_image")
            ],
            [
                InlineKeyboardButton("📊 Statistics", callback_data="statistics"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Enhanced error handling for message editing
        try:
            await query.edit_message_text(
                response_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.info(f"✅ Successfully reformatted to {format_type}")
            
        except Exception as message_error:
            logger.warning(f"Message edit failed, sending new message: {message_error}")
            # Fallback: send as new message
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=response_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        
    except Exception as e:
        logger.error(f"❌ Error in reformat: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Ultimate fallback - show original text
        try:
            original_text = context.user_data.get(f'original_text_{original_message_id}', 'No text available')
            await query.edit_message_text(
                f"❌ *Reformatting Error*\n\n"
                f"Showing original text:\n\n"
                f"{original_text}",
                parse_mode='Markdown'
            )
        except Exception as final_error:
            logger.error(f"Final fallback failed: {final_error}")
            await query.edit_message_text(
                "❌ *System Error*\n\n"
                "Reformatting failed. Please process the image again.",
                parse_mode='Markdown'
            )

async def handle_convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle convert image callback with enhanced messaging"""
    query = update.callback_query
    await query.answer("📸 Ready for your image!")
    
    await query.edit_message_text(
        "📸 *Ready for Image Processing*\n\n"
        "Send me an image containing text and I'll extract it for you.\n\n"
        "🎯 *For Best Results:*\n"
        "• Clear, high-quality images\n"
        "• Good lighting and contrast\n"
        "• Horizontal text alignment\n"
        "• Focused, readable text\n\n"
        "🌍 *Supported Content:*\n"
        "• Documents and printed text\n"
        "• Signs, menus, books\n"
        "• Screenshots with text\n"
        "• Photos of text content\n\n"
        "⚡ *Automatic Features:*\n"
        "• Multi-language detection\n"
        "• Format preservation\n"
        "• Bullet point recognition\n"
        "• Structure maintenance",
        parse_mode='Markdown'
    )

async def handle_ocr_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show OCR statistics with enhanced metrics"""
    query = update.callback_query
    await query.answer()
    
    try:
        stats = performance_monitor.get_stats()
        db = context.bot_data.get('db')
        user_id = query.from_user.id
        
        # Get user-specific stats if available
        user_stats = {}
        if db:
            try:
                user_stats = db.get_user_stats(user_id)
            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
        
        response_text = (
            "📊 *OCR Performance Statistics*\n\n"
            f"• ⏱️ Average Processing Time: `{stats.get('avg_time', 0):.2f}s`\n"
            f"• 🎯 System Accuracy: `{stats.get('avg_confidence', 0):.1f}%`\n"
            f"• ✅ Success Rate: `{stats.get('success_rate', 0):.1f}%`\n"
            f"• 📈 Total Requests: `{stats.get('total_requests', 0)}`\n"
        )
        
        # Add user-specific stats if available
        if user_stats:
            response_text += (
                f"\n👤 *Your Usage:*\n"
                f"• 📊 Your Requests: `{user_stats.get('total_requests', 0)}`\n"
                f"• 🎯 Your Success Rate: `{user_stats.get('success_rate', 0):.1f}%`\n"
                f"• 📝 Recent Activity: `{len(user_stats.get('recent_requests', []))} requests`\n"
            )
        
        response_text += (
            f"\n⚡ *System Status:*\n"
            f"• 🟢 Production Ready\n"
            f"• 🔄 Active Processing\n"
            f"• 🌍 Multi-language Support\n"
            f"• 📷 Image Optimization\n\n"
            f"💡 *Performance Tips:*\n"
            f"• Optimal image size: 1-5MB\n"
            f"• Best format: JPEG/PNG\n"
            f"• Text should be clearly readable\n"
            f"• Good lighting improves accuracy"
        )
        
        keyboard = [
            [InlineKeyboardButton("📸 Process Image", callback_data="convert_image")],
            [InlineKeyboardButton("🔄 Refresh Stats", callback_data="statistics")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        await query.edit_message_text(
            "❌ *Statistics Unavailable*\n\n"
            "Performance data is currently unavailable.\n"
            "Please try again later.",
            parse_mode='Markdown'
        )

# OCR callback handler
async def handle_ocr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all OCR-related callbacks with enhanced routing"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    try:
        if callback_data.startswith("reformat_"):
            await handle_reformat(update, context)
        elif callback_data == "convert_image":
            await handle_convert_image(update, context)
        elif callback_data == "statistics":
            await handle_ocr_statistics(update, context)
        else:
            await query.edit_message_text(
                "❌ *Unknown Command*\n\n"
                "The requested action is not available.\n"
                "Returning to main menu...",
                parse_mode='Markdown'
            )
            # You might want to redirect to main menu here
            
    except Exception as e:
        logger.error(f"Callback handler error: {e}")
        await query.edit_message_text(
            "❌ *System Error*\n\n"
            "An error occurred while processing your request.\n"
            "Please try again.",
            parse_mode='Markdown'
        )

# Additional utility functions
def get_processing_status(user_id: int) -> bool:
    """Check if user has active processing"""
    return user_id in processing_cache

def cleanup_old_cache():
    """Clean up old cache entries"""
    current_time = time.time()
    expired_users = [
        user_id for user_id, data in processing_cache.items()
        if current_time - data['timestamp'] > CACHE_TIMEOUT
    ]
    for user_id in expired_users:
        processing_cache.pop(user_id, None)
    
    if expired_users:
        logger.info(f"Cleaned up {len(expired_users)} expired cache entries")

# Periodic cleanup (you can call this from your main app)
async def periodic_cleanup():
    """Periodic cleanup of processing cache"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        cleanup_old_cache()