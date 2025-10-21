# handlers/start.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from handlers.menu import show_main_menu
import config
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced /start command with better format explanation and Amharic support"""
    user = update.effective_user
    
    logger.info(f"🚀 /start from user {user.id} (@{user.username})")
    
    # Get database from bot_data
    db = context.bot_data.get('db')
    
    # Check channel membership
    has_joined = await check_channel_membership(update, context, user.id)
    
    if not has_joined:
        logger.info(f"❌ User {user.id} not in channel")
        await show_channel_requirement(update, context)
        return
    
    # User has joined, proceed
    logger.info(f"✅ User {user.id} verified, proceeding")
    from_callback = update.callback_query is not None
    await process_user_start(update, context, user, db, from_callback=from_callback)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Check if user is a member of the announcement channel"""
    try:
        logger.info(f"🔍 Checking membership for user {user_id}")
        
        chat_member = await context.bot.get_chat_member(
            chat_id=config.ANNOUNCEMENT_CHANNEL,
            user_id=user_id
        )
        
        logger.info(f"📊 User {user_id} status: {chat_member.status}")
        
        if chat_member.status not in ['left', 'kicked', 'banned']:
            logger.info(f"✅ User {user_id} is a channel member")
            return True
        else:
            logger.info(f"❌ User {user_id} not in channel (status: {chat_member.status})")
            return False
        
    except Exception as e:
        logger.error(f"🚨 Error checking membership for user {user_id}: {e}")
        try:
            chat = await context.bot.get_chat(config.ANNOUNCEMENT_CHANNEL)
            logger.warning(f"⚠️ Bot can access channel {chat.title} but can't check membership")
            return False
        except Exception as e2:
            logger.error(f"🚨 Bot cannot access channel {config.ANNOUNCEMENT_CHANNEL}: {e2}")
            await update.effective_message.reply_text(
                f"❌ Error: Bot cannot access the channel @{config.CHANNEL_USERNAME}. "
                "Please ensure the bot is an admin in the channel and try again."
            )
            return False

async def show_channel_requirement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel join requirement"""
    keyboard = [
        [InlineKeyboardButton("📢 Join Announcement Channel", url=f"https://t.me/{config.CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "👋 *Welcome to Enhanced OCR Bot!* 📸\n\n"
        "📢 *Join Our Channel First*\n\n"
        "Please join our channel to use this bot:\n"
        "• 🚀 Get updates and new features\n"
        "• 💡 Learn usage tips\n"
        "• 🌍 Amharic language support\n"
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
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.effective_message.reply_text(
                message_text,
                reply_markup=reply_markup,
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
    
    db = context.bot_data.get('db')
    
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        logger.info(f"🎉 User {user.id} verified successfully")
        await query.edit_message_text("✅ Thank you for joining! Setting up your account...")
        await process_user_start(update, context, user, db, from_callback=True)
    else:
        logger.warning(f"❌ User {user.id} not verified")
        await query.answer(
            "❌ Please join the channel and wait a moment before clicking 'I've Joined'.",
            show_alert=True
        )

async def process_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user, db=None, from_callback=False):
    """Enhanced user start processing with better format explanation"""
    try:
        # Initialize user with plain text as default format
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'joined_channel': True,
            'channel_join_date': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'settings': {
                'text_format': 'plain',  # Default to plain text
                'language_preference': 'auto',  # Auto-detect language
                'updated_at': datetime.now()
            }
        }
        
        if db:
            try:
                # Check if user exists, update if they do
                existing_user = db.get_user(user.id)
                if existing_user:
                    # Update existing user's last active time
                    db.update_user_settings(user.id, {'last_active': datetime.now()})
                    logger.info(f"✅ Updated existing user {user.id}")
                else:
                    # Insert new user
                    result = db.insert_user(user_data)
                    logger.info(f"✅ New user {user.id} saved to database")
            except Exception as e:
                logger.error(f"❌ Error saving user {user.id}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error processing user {user.id}: {e}")
    
    # Enhanced welcome message with clear format explanation
    welcome_text = (
        f"🎉 *Welcome {user.first_name}!* 🌍\n\n"
        "🤖 *Enhanced OCR Bot with Amharic Support*\n\n"
        "✨ *Enhanced Features:*\n"
        "• 🚀 Advanced text extraction\n"
        "• 🌍 **Amharic language support**\n"
        "• 📸 Blurry image processing\n"
        "• 💬 **Default: Plain Text** (clean & readable)\n"
        "• 📋 **HTML Format** (copy-friendly)\n"
        "• 🔤 Auto language detection\n"
        "• 💾 Your preferences saved\n\n"
        "📸 *How to use:*\n"
        "1. Send me any image with text\n"
        "2. I'll extract and format the text\n"
        "3. Choose between formats:\n"
        "   • 📄 **Plain Text** (default, best for reading)\n"
        "   • 🌐 **HTML** (preserves formatting, easy to copy)\n\n"
        "🌍 *Amharic Support:*\n"
        "• Send Amharic text images\n"
        "• Automatic script detection\n"
        "• Optimized for Ethiopic characters\n\n"
        "💡 *For best results:*\n"
        "• Clear, well-lit images\n"
        "• Focused, non-blurry text\n"
        "• High contrast\n"
        "• Horizontal text alignment\n\n"
        "Use the menu below or the pinned message to explore! 🎯"
    )
    
    if db and hasattr(db, 'is_mock') and db.is_mock:
        welcome_text += "\n\n⚠️ *Note:* Using temporary storage (data resets on restart)"
    else:
        welcome_text += "\n\n💾 *Storage:* Your preferences are saved permanently"
    
    # Send welcome message
    if from_callback:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(welcome_text, parse_mode='Markdown')
    
    # Enhanced persistent keyboard with better labels
    keyboard = [
        ['📸 Convert Image', '⚙️ Settings'],
        ['📊 Statistics', '❓ Help'],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
        input_field_placeholder='Choose an option or send an image...'
    )
    
    await update.effective_message.reply_text(
        "📱 *Use the menu below:*\n• Send images directly\n• Or use buttons to navigate",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Show main menu
    await show_main_menu(update, context)

async def force_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force check channel membership"""
    user = update.effective_user
    logger.info(f"🔧 Force membership check for user {user.id}")
    
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        await update.effective_message.reply_text(
            "✅ *Channel Membership Verified!*\n\n"
            "You are a confirmed member. Thank you! 🎉\n\n"
            "You can now use all features including Amharic text extraction.",
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

def get_user_settings(db, user_id):
    """Get user settings with safe defaults"""
    try:
        if db and hasattr(db, 'get_user'):
            user = db.get_user(user_id)
            if user and 'settings' in user:
                return user['settings']
    except Exception as e:
        logger.error(f"Error getting settings for user {user_id}: {e}")
    
    # Return safe defaults
    return {
        'text_format': 'plain',  # Default to plain text
        'language_preference': 'auto',
        'updated_at': datetime.now()
    }

def update_user_settings(db, user_id, settings_update):
    """Update user settings safely"""
    try:
        if db and hasattr(db, 'update_user_settings'):
            # Get current settings first
            current_settings = get_user_settings(db, user_id)
            # Merge with updates
            updated_settings = {**current_settings, **settings_update, 'updated_at': datetime.now()}
            # Save to database
            success = db.update_user_settings(user_id, updated_settings)
            if success:
                logger.info(f"✅ Updated settings for user {user_id}: {settings_update}")
                return True
    except Exception as e:
        logger.error(f"❌ Error updating settings for user {user_id}: {e}")
    
    return False