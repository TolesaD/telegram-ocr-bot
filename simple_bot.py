import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token - REPLACE WITH YOUR ACTUAL TOKEN!
BOT_TOKEN = "8452300221:AAHj8GaG_hE5OLaQslUl2I8b1rW8zCqYWG4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('''
🤖 Welcome to Reminder Bot!

I'll help you set reminders so you never forget anything important!

Available commands:
• /setreminder <time> <message> [recurrence] - Set a new reminder
• /viewreminders - View all your active reminders
• /cancelreminder <id> - Cancel a specific reminder

Examples:
• /setreminder 09:00 Drink water daily
• /setreminder 18:30 Team meeting weekly
• /setreminder 15:00 Pay bills monthly

Time format: HH:MM (24-hour format)
Recurrence: daily, weekly, monthly (optional)
    ''')

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a reminder"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Please provide both time and message.\n"
            "Usage: /setreminder <HH:MM> <message> [recurrence]"
        )
        return
    
    time_str = context.args[0]
    message = ' '.join(context.args[1:])
    
    await update.message.reply_text(
        f"✅ Reminder set successfully!\n"
        f"⏰ Time: {time_str}\n"
        f"📝 Message: {message}\n"
        f"🔔 Note: Running in test mode (no database)"
    )

async def view_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all reminders"""
    await update.message.reply_text(
        "📭 Running in test mode - no reminders stored\n"
        "Set up MongoDB to save reminders permanently"
    )

async def cancel_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel a reminder"""
    await update.message.reply_text(
        "❌ Running in test mode - no reminders to cancel\n"
        "Set up MongoDB to manage reminders"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages"""
    await update.message.reply_text(
        "🤖 I'm a reminder bot! Use /start to see available commands."
    )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setreminder", set_reminder))
    application.add_handler(CommandHandler("viewreminders", view_reminders))
    application.add_handler(CommandHandler("cancelreminder", cancel_reminder))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    logger.info("Bot starting in polling mode...")
    application.run_polling()

if __name__ == '__main__':
    main()