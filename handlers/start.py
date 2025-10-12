from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from database.mongodb import db
from handlers.menu import show_main_menu
import config
import logging

logger = logging.getLogger(__name__)

# Your announcement channel details - UPDATE THESE WITH YOUR ACTUAL CHANNEL!
ANNOUNCEMENT_CHANNEL = "@BusinessAfaanOro"  # Change this to your actual channel (with @)
CHANNEL_USERNAME = "BusinessAfaanOro"       # Change this to your actual channel (without @)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with channel verification"""
    user = update.effective_user
    
    logger.info(f"🚀 /start command from user {user.id} ({user.username})")
    
    # Check if user has joined the channel
    has_joined = await check_channel_membership(update, context, user.id)
    
    if not has_joined:
        logger.info(f"❌ User {user.id} has not joined channel, showing requirement")
        await show_channel_requirement(update, context)
        return
    
    # User has joined the channel, proceed with normal start
    logger.info(f"✅ User {user.id} has joined channel, proceeding with start")
    await process_user_start(update, context, user)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Check if user is a member of the announcement channel"""
    try:
        logger.info(f"🔍 Checking membership for user {user_id} in channel {ANNOUNCEMENT_CHANNEL}")
        
        # Try to get chat member - this will raise an error if user is not a member or bot doesn't have permissions
        chat_member = await context.bot.get_chat_member(
            chat_id=ANNOUNCEMENT_CHANNEL,
            user_id=user_id
        )
        
        logger.info(f"📊 User {user_id} status in channel: {chat_member.status}")
        
        # Check if user status is not "left" (meaning they've joined)
        if chat_member.status not in ['left', 'kicked', 'banned']:
            logger.info(f"✅ User {user_id} is a channel member")
            return True
        else:
            logger.info(f"❌ User {user_id} has not joined the channel (status: {chat_member.status})")
            return False
        
    except Exception as e:
        logger.error(f"🚨 Error checking channel membership for user {user_id}: {e}")
        
        # Try alternative method - check if bot can access the chat at all
        try:
            chat = await context.bot.get_chat(ANNOUNCEMENT_CHANNEL)
            logger.info(f"📢 Bot can access chat: {chat.title} (ID: {chat.id})")
            logger.warning("⚠️ Bot can access chat but cannot check user membership - this usually means bot is not admin")
            logger.warning("💡 Make sure the bot is an admin in the channel with 'Ban users' permission")
            
            # For testing, you can return True here to bypass the requirement
            # In production, you should return False to enforce the requirement
            return False  # Change to True for testing if needed
            
        except Exception as e2:
            logger.error(f"🚨 Bot cannot access chat at all: {e2}")
            logger.error("💡 Check: 1) Channel exists 2) Bot is in channel 3) Channel username is correct")
            return False  # Require joining if bot can't even access the chat

async def show_channel_requirement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel join requirement message"""
    keyboard = [
        [InlineKeyboardButton("📢 Join Announcement Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "👋 *Welcome to Image-to-Text Converter Bot!*\n\n"
        "📢 *Join Our Announcement Channel First*\n\n"
        "To use this bot and access all features, please join our announcement channel to stay updated with:\n"
        "• 🚀 New features and updates\n"
        "• 💡 Usage tips and tutorials\n"
        "• 🔧 Maintenance announcements\n"
        "• 📢 Community news and updates\n\n"
        "*How to proceed:*\n"
        "1. Click *'Join Announcement Channel'* below\n"
        "2. Join the channel\n"
        "3. Return here and click *'I've Joined'*\n"
        "4. Start using the bot!\n\n"
        "We promise to keep announcements minimal and valuable! ✨"
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
    
    logger.info(f"🔄 User {user.id} clicked 'I've Joined', checking membership...")
    
    # Check membership again
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        logger.info(f"🎉 User {user.id} successfully verified channel membership")
        await query.edit_message_text("✅ Thank you for joining! Setting up your account...")
        await process_user_start(update, context, user, from_callback=True)
    else:
        logger.warning(f"❌ User {user.id} clicked 'I've Joined' but not actually joined")
        await query.answer(
            "❌ We couldn't verify that you've joined the channel. Please make sure:\n\n"
            "• You actually joined the channel\n"
            "• You didn't leave immediately after joining\n"
            "• The channel username is correct\n\n"
            "If issues persist, try joining again and wait a moment before clicking this button.",
            show_alert=True
        )

async def process_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user, from_callback=False):
    """Process user start after channel verification"""
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
        
        # Save user to database
        result = db.insert_user(user_data)
        
        if result:
            logger.info(f"✅ User {user.id} saved to database with channel membership")
        else:
            logger.warning(f"⚠️ User {user.id} not saved to database (using mock storage)")
        
    except Exception as e:
        logger.error(f"❌ Error saving user {user.id}: {e}")
    
    welcome_text = (
        f"🎉 *Welcome {user.first_name}!*\n\n"
        "🤖 *Image-to-Text Converter Bot*\n\n"
        "✨ *Premium Features Now Unlocked:*\n"
        "• 🚀 Fast text extraction (optimized processing)\n"
        "• 🔍 Enhanced image recognition\n"
        "• 🌐 Multi-language OCR support\n"
        "• 📝 Multiple text formats\n"
        "• 💾 User preferences saved\n\n"
        "📸 *How to get started:*\n"
        "1. Send me any image containing text\n"
        "2. I'll extract and format the text for you\n"
        "3. Choose your preferred output format\n\n"
        "💡 *Pro tips for best results:*\n"
        "• Use clear, well-lit images\n"
        "• Ensure text is focused and not blurry\n"
        "• High contrast works best (dark text on light background)\n"
        "• Crop to just the text area for faster processing\n\n"
    )
    
    # Add database status to welcome message
    if db.is_mock:
        welcome_text += "💾 *Storage:* Temporary (settings will reset on bot restart)\n\n"
    else:
        welcome_text += "💾 *Storage:* Permanent (your settings are saved)\n\n"
    
    welcome_text += "Use the menu below to explore all features! 🎯"
    
    if from_callback:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown')
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        await show_main_menu(update, context)

async def force_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force check channel membership (admin command)"""
    user = update.effective_user
    logger.info(f"🔧 Admin membership check for user {user.id}")
    
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        await update.message.reply_text(
            "✅ *Channel Membership Verified!*\n\n"
            "You are a confirmed member of our announcement channel. "
            "Thank you for being part of our community! 🎉",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Channel Membership Required*\n\n"
            "You need to join our announcement channel to use this bot.\n\n"
            "Please use `/start` to begin the channel verification process.",
            parse_mode='Markdown'
        )

async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel information (admin/debug command)"""
    try:
        chat = await context.bot.get_chat(ANNOUNCEMENT_CHANNEL)
        
        info_text = (
            f"📢 *Channel Information*\n\n"
            f"• **Title:** {chat.title}\n"
            f"• **Username:** @{chat.username}\n"
            f"• **ID:** `{chat.id}`\n"
            f"• **Type:** {chat.type}\n"
            f"• **Description:** {chat.description or 'No description'}\n\n"
            f"**Bot Configuration:**\n"
            f"• ANNOUNCEMENT_CHANNEL: `{ANNOUNCEMENT_CHANNEL}`\n"
            f"• CHANNEL_USERNAME: `{CHANNEL_USERNAME}`\n"
        )
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Error accessing channel:*\n\n`{e}`\n\n"
            "Please check:\n"
            "1. Channel username is correct\n"
            "2. Bot is added to the channel\n"
            "3. Bot has appropriate permissions",
            parse_mode='Markdown'
        )