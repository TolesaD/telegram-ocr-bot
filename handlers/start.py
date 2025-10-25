# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from datetime import datetime
import config
import logging

logger = logging.getLogger(__name__)

# Store user verification status to avoid repeated checks
user_verification_cache = {}

def get_main_keyboard():
    """Get the main inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("📸 Convert Image", callback_data="convert_image")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Statistics", callback_data="statistics")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channel_keyboard():
    """Get channel join keyboard"""
    keyboard = [
        [InlineKeyboardButton("📢 Join Announcement Channel", url=f"https://t.me/{config.CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Check if user is a member of the announcement channel with caching"""
    # Check cache first
    if user_id in user_verification_cache:
        cached_status = user_verification_cache[user_id]
        # Cache expires after 1 hour
        if (datetime.now() - cached_status['timestamp']).total_seconds() < 3600:
            logger.info(f"🎯 Using cached membership status for user {user_id}: {cached_status['status']}")
            return cached_status['status']
    
    try:
        logger.info(f"🔍 Checking membership for user {user_id}")
        
        chat_member = await context.bot.get_chat_member(
            chat_id=config.ANNOUNCEMENT_CHANNEL,
            user_id=user_id
        )
        
        logger.info(f"📊 User {user_id} status: {chat_member.status}")
        
        is_member = chat_member.status not in ['left', 'kicked', 'banned']
        
        # Update cache
        user_verification_cache[user_id] = {
            'status': is_member,
            'timestamp': datetime.now()
        }
        
        if is_member:
            logger.info(f"✅ User {user_id} is a channel member")
            return True
        else:
            logger.info(f"❌ User {user_id} not in channel")
            return False
        
    except Exception as e:
        logger.error(f"🚨 Error checking membership for user {user_id}: {e}")
        # If bot can't access channel, allow user to proceed but don't cache
        return True

async def require_channel_membership(handler):
    """Decorator to require channel membership for any handler"""
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # Skip verification for admins
        if user.id in config.ADMIN_IDS:
            return await handler(update, context)
        
        # Check membership
        has_joined = await check_channel_membership(update, context, user.id)
        
        if not has_joined:
            logger.info(f"🚫 Blocking user {user.id} - not in channel")
            await show_channel_requirement(update, context)
            return
        
        # User is verified, proceed with original handler
        return await handler(update, context)
    
    return wrapped

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with channel requirement"""
    user = update.effective_user
    
    logger.info(f"🚀 /start from user {user.id} (@{user.username})")
    
    # Check channel membership first
    has_joined = await check_channel_membership(update, context, user.id)
    
    if not has_joined:
        logger.info(f"❌ User {user.id} not in channel")
        await show_channel_requirement(update, context)
        return
    
    # User has joined, proceed to main menu
    logger.info(f"✅ User {user.id} verified, proceeding")
    await process_user_start(update, context, user)

async def show_channel_requirement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel join requirement"""
    message_text = (
        "👋 *Welcome to Enhanced OCR Bot!* 📸\n\n"
        "📢 *Join Our Channel First*\n\n"
        "Please join our channel to use this bot:\n"
        "• 🚀 Get updates and new features\n"
        "• 💡 Learn usage tips\n"
        "• 🌍 70+ language support\n"
        "• 🔧 Stay informed about maintenance\n\n"
        "*Steps:*\n"
        "1. Click 'Join Announcement Channel'\n"
        "2. Join the channel\n"
        "3. Click 'I've Joined'\n"
        "4. Start converting images! 🎉"
    )
    
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=get_channel_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await update.effective_message.reply_text(
                message_text,
                reply_markup=get_channel_keyboard(),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"❌ Error sending channel requirement message: {e}")
        await update.effective_message.reply_text(
            "❌ Error displaying channel join message. Please try again or contact support."
        )

async def handle_membership_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle membership check callback"""
    query = update.callback_query
    user = query.from_user
    
    await query.answer()
    
    logger.info(f"🔄 User {user.id} checking membership...")
    
    # Clear cache to force fresh check
    if user.id in user_verification_cache:
        del user_verification_cache[user.id]
    
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        logger.info(f"🎉 User {user.id} verified successfully")
        await query.edit_message_text("✅ Thank you for joining! Setting up your account...")
        await process_user_start(update, context, user, from_callback=True)
    else:
        logger.warning(f"❌ User {user.id} not verified")
        await query.answer(
            "❌ Please join the channel and wait a moment before clicking 'I've Joined'.",
            show_alert=True
        )

async def process_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user, from_callback=False):
    """Process user after channel verification"""
    # Get database from bot_data
    db = context.bot_data.get('db')
    
    # Save user data - only if it's not a mock database
    if db and not getattr(db, 'is_mock', False):
        try:
            user_data = {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'joined_channel': True,
                'channel_join_date': datetime.now(),
                'settings': {'text_format': 'plain'}
            }
            db.insert_user(user_data)
            logger.info(f"✅ User {user.id} saved to database")
        except Exception as e:
            logger.error(f"❌ Error saving user {user.id}: {e}")
    
    welcome_text = (
        f"🎉 *Welcome {user.first_name}!* 🌍\n\n"
        "🤖 *Enhanced OCR Bot with 70+ Language Support*\n\n"
        "✨ *Features:*\n"
        "• 🚀 Advanced text extraction\n"
        "• 🌍 **70+ languages supported**\n"
        "• 💬 **Plain Text & HTML formats**\n"
        "• 🔤 Auto language detection\n\n"
        "📸 *How to use:*\n"
        "1. Send me any image with text\n"
        "2. I'll extract and format the text automatically\n\n"
        "💡 *For best results:*\n"
        "• Clear, well-lit images\n"
        "• Focused, non-blurry text\n"
        "• High contrast\n"
        "• Horizontal text alignment"
    )
    
    # Import reply keyboard from app
    try:
        from app import get_reply_keyboard
        reply_markup = get_reply_keyboard()
    except ImportError:
        from app import get_main_keyboard
        reply_markup = get_main_keyboard()
    
    # Send welcome message
    try:
        if from_callback:
            await update.callback_query.edit_message_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.effective_message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        # Fallback: send new message if edit fails
        if from_callback:
            await update.callback_query.message.reply_text(
                welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def force_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force check channel membership"""
    user = update.effective_user
    logger.info(f"🔧 Force membership check for user {user.id}")
    
    # Clear cache
    if user.id in user_verification_cache:
        del user_verification_cache[user.id]
    
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        await update.effective_message.reply_text(
            "✅ *Channel Membership Verified!*\n\n"
            "You are a confirmed member. Thank you! 🎉\n\n"
            "You can now use all features including 70+ language text extraction.",
            parse_mode='Markdown'
        )
    else:
        await update.effective_message.reply_text(
            "❌ *Channel Membership Required!*\n\n"
            "Please join our channel and use `/start` to verify and access all features.",
            parse_mode='Markdown'
        )

async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start-related callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_membership":
        await handle_membership_check(update, context)
    elif query.data == "restart_bot":
        await query.answer("🔄 Restarting bot...")
        await start_command(update, context)

# Export the decorator for use in other handlers
__all__ = ['require_channel_membership', 'start_command', 'check_channel_membership']