from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from handlers.menu import show_main_menu
import config
import logging

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with improved channel verification"""
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
    await process_user_start(update, context, user, db)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Check if user is a member of the announcement channel"""
    try:
        logger.info(f"🔍 Checking membership for user {user_id}")
        
        chat_member = await context.bot.get_chat_member(
            chat_id=config.ANNOUNCEMENT_CHANNEL,
            user_id=user_id
        )
        
        logger.info(f"📊 User {user_id} status: {chat_member.status}")
        
        # Check if user is a member (not left, kicked, or banned)
        if chat_member.status not in ['left', 'kicked', 'banned']:
            logger.info(f"✅ User {user_id} is a channel member")
            return True
        else:
            logger.info(f"❌ User {user_id} not in channel (status: {chat_member.status})")
            return False
        
    except Exception as e:
        logger.error(f"🚨 Error checking membership: {e}")
        
        # Try to verify bot can access the channel
        try:
            chat = await context.bot.get_chat(config.ANNOUNCEMENT_CHANNEL)
            logger.warning(f"⚠️ Bot can access {chat.title} but can't check membership")
            logger.warning("💡 Make sure bot is admin with 'Ban users' permission")
            
            # For production, return False to enforce requirement
            return False
            
        except Exception as e2:
            logger.error(f"🚨 Bot cannot access channel: {e2}")
            return False

async def show_channel_requirement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel join requirement"""
    keyboard = [
        [InlineKeyboardButton("📢 Join Announcement Channel", url=f"https://t.me/{config.CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "👋 *Welcome to Image-to-Text Converter Bot!*\n\n"
        "📢 *Join Our Announcement Channel First*\n\n"
        "To use this bot, please join our channel for:\n"
        "• 🚀 New features and updates\n"
        "• 💡 Usage tips and tutorials\n"
        "• 🔧 Maintenance announcements\n"
        "• 📢 Important news\n\n"
        "*How to proceed:*\n"
        "1. Click *'Join Announcement Channel'*\n"
        "2. Join the channel\n"
        "3. Return and click *'I've Joined'*\n"
        "4. Start converting images! 🎉\n\n"
        "We keep announcements minimal and valuable! ✨"
    )
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_membership_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle membership check callback"""
    query = update.callback_query
    user = query.from_user
    
    await query.answer()
    
    logger.info(f"🔄 User {user.id} checking membership...")
    
    # Get database from bot_data
    db = context.bot_data.get('db')
    
    # Check membership again
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        logger.info(f"🎉 User {user.id} verified successfully")
        await query.edit_message_text("✅ Thank you for joining! Setting up your account...")
        await process_user_start(update, context, user, db, from_callback=True)
    else:
        logger.warning(f"❌ User {user.id} not verified")
        await query.answer(
            "❌ We couldn't verify your channel membership.\n\n"
            "Please ensure:\n"
            "• You actually joined the channel\n"
            "• You didn't leave immediately\n"
            "• The join was completed\n\n"
            "Try joining again and wait a moment before clicking.",
            show_alert=True
        )

async def process_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user, db=None, from_callback=False):
    """Process user start after verification"""
    try:
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
                'language': 'english',
                'text_format': 'plain',
                'updated_at': datetime.now()
            }
        }
        
        # Save user to database if available
        if db:
            try:
                result = db.insert_user(user_data)
                
                if result:
                    logger.info(f"✅ User {user.id} saved to database")
                else:
                    logger.warning(f"⚠️ User {user.id} storage failed")
            except Exception as e:
                logger.error(f"❌ Error saving user {user.id}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error processing user {user.id}: {e}")
    
    welcome_text = (
        f"🎉 *Welcome {user.first_name}!*\n\n"
        "🤖 *Image-to-Text Converter Bot*\n\n"
        "✨ *Features:*\n"
        "• 🚀 Optimized text extraction\n"
        "• 🔍 Multi-language OCR support\n"
        "• 📝 Multiple text formats\n"
        "• 💾 Your preferences saved\n\n"
        "📸 *How to use:*\n"
        "1. Send me any image with text\n"
        "2. I'll extract and format the text\n"
        "3. Choose your preferred format\n\n"
        "💡 *For best results:*\n"
        "• Clear, well-lit images\n"
        "• Focused, non-blurry text\n"
        "• High contrast\n"
        "• Crop to text area\n\n"
    )
    
    # Add storage info
    if db and hasattr(db, 'is_mock') and db.is_mock:
        welcome_text += "💾 *Storage:* Temporary (reset on restart)\n\n"
    else:
        welcome_text += "💾 *Storage:* Permanent settings\n\n"
    
    welcome_text += "Use the menu below to explore! 🎯"
    
    if from_callback:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown')
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        await show_main_menu(update, context)

async def force_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force check channel membership"""
    user = update.effective_user
    logger.info(f"🔧 Force membership check for user {user.id}")
    
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        await update.message.reply_text(
            "✅ *Channel Membership Verified!*\n\n"
            "You are a confirmed member. Thank you! 🎉",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Channel Membership Required*\n\n"
            "Please join our channel and use `/start` to verify.",
            parse_mode='Markdown'
        )