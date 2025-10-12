from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from database.mongodb import db
from handlers.menu import show_main_menu
import config

# Your announcement channel details - UPDATE THESE!
ANNOUNCEMENT_CHANNEL = "@BusinessAfaanOro"  # Change this to your actual channel
CHANNEL_USERNAME = "BusinessAfaanOro"  # Without @

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with channel verification"""
    user = update.effective_user
    
    # Check if user has joined the channel
    has_joined = await check_channel_membership(update, context, user.id)
    
    if not has_joined:
        await show_channel_requirement(update, context)
        return
    
    # User has joined the channel, proceed with normal start
    await process_user_start(update, context, user)

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Check if user is a member of the announcement channel"""
    try:
        # Try to get chat member - this will raise an error if user is not a member
        chat_member = await context.bot.get_chat_member(
            chat_id=ANNOUNCEMENT_CHANNEL,
            user_id=user_id
        )
        
        # Check if user status is not "left" (meaning they've joined)
        if chat_member.status not in ['left', 'kicked', 'banned']:
            return True
        
        return False
        
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        # If we can't check (bot not admin, etc.), allow access
        return True

async def show_channel_requirement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel join requirement message"""
    keyboard = [
        [InlineKeyboardButton("📢 Join Announcement Channel", url=f"https://t.me/{BusinessAfaanOro}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "👋 *Welcome!*\n\n"
        "📢 *Join Our Announcement Channel First*\n\n"
        "To use this bot, please join our announcement channel to stay updated with:\n"
        "• New features and updates\n"
        "• Usage tips and tutorials\n"
        "• Maintenance announcements\n"
        "• Community news\n\n"
        "After joining, click *'I've Joined'* to continue."
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
    
    # Check membership again
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        await query.edit_message_text("✅ Thank you for joining! Setting up your account...")
        await process_user_start(update, context, user, from_callback=True)
    else:
        await query.answer("❌ Please join the channel first!", show_alert=True)

async def process_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE, user, from_callback=False):
    """Process user start after channel verification"""
    try:
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'joined_channel': True,
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
            print(f"✅ User {user.id} saved to database")
        else:
            print(f"⚠️  User {user.id} not saved (using mock database)")
        
    except Exception as e:
        print(f"❌ Error saving user: {e}")
    
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "🤖 *Welcome to Image to Text Converter Bot*\n\n"
        "✨ *Enhanced Features:*\n"
        "• Fast text extraction (optimized processing)\n"
        "• Better image recognition (low-quality support)\n"
        "• Multi-language OCR support\n"
        "• Multiple text formats\n\n"
        "📸 *How to use:*\n"
        "1. Send me an image containing text\n"
        "2. I'll quickly extract and send you the text\n"
        "3. Choose your preferred text format\n\n"
        "💡 *Tips for best results:*\n"
        "• Clear, well-lit images work best\n"
        "• Straight, focused photos\n"
        "• High contrast text\n\n"
    )
    
    # Add database status to welcome message
    if db.is_mock:
        welcome_text += "⚠️ *Note:* Using temporary storage\n\n"
    else:
        welcome_text += "✅ *Database:* Connected\n\n"
    
    welcome_text += "Use the menu below to get started!"
    
    if from_callback:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown')
        await show_main_menu(update, context)
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        await show_main_menu(update, context)

async def force_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force check channel membership (admin command)"""
    user = update.effective_user
    has_joined = await check_channel_membership(update, context, user.id)
    
    if has_joined:
        await update.message.reply_text("✅ You are a member of the announcement channel!")
    else:
        await update.message.reply_text("❌ Please join our announcement channel to use the bot.")