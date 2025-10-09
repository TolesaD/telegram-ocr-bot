from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class CommandHandlers:
    def __init__(self, reminder_manager):
        self.reminder_manager = reminder_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
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
        """
        await update.message.reply_text(welcome_text)
    
    async def set_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Please provide both time and message.\n"
                "Usage: /setreminder <HH:MM> <message> [recurrence]"
            )
            return
        
        # Parse arguments
        time_str = context.args[0]
        recurrence = None
        
        # Check for recurrence at the end
        if context.args[-1].lower() in ['daily', 'weekly', 'monthly']:
            recurrence = context.args[-1].lower()
            message = ' '.join(context.args[1:-1])
        else:
            message = ' '.join(context.args[1:])
        
        # Validate time format
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
            await update.message.reply_text(
                "❌ Invalid time format. Please use HH:MM (24-hour format)"
            )
            return
        
        try:
            reminder_id = self.reminder_manager.create_reminder(
                user_id=update.effective_user.id,
                chat_id=update.effective_chat.id,
                time=time_str,
                message=message,
                recurrence=recurrence
            )
            
            recurrence_text = f" ({recurrence})" if recurrence else ""
            await update.message.reply_text(
                f"✅ Reminder set successfully!\n"
                f"⏰ Time: {time_str}{recurrence_text}\n"
                f"📝 Message: {message}\n"
                f"🆔 ID: {reminder_id}"
            )
            
        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            await update.message.reply_text("❌ Failed to set reminder. Please try again.")
    
    async def view_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        reminders = self.reminder_manager.get_user_reminders(user_id)
        
        if not reminders:
            await update.message.reply_text("📭 You have no active reminders.")
            return
        
        reminders_text = "📋 Your Active Reminders:\n\n"
        for reminder in reminders:
            recurrence_text = f" ({reminder['recurrence']})" if reminder['recurrence'] else ""
            reminders_text += (
                f"🆔 {reminder['_id']}\n"
                f"⏰ {reminder['time']}{recurrence_text}\n"
                f"📝 {reminder['message']}\n"
                f"⏳ Next: {reminder['next_reminder'].strftime('%Y-%m-%d %H:%M')}\n"
                f"────────────────────\n"
            )
        
        await update.message.reply_text(reminders_text)
    
    async def cancel_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide reminder ID.\n"
                "Usage: /cancelreminder <reminder_id>\n"
                "Use /viewreminders to see your reminder IDs"
            )
            return
        
        reminder_id = context.args[0]
        user_id = update.effective_user.id
        
        try:
            success = self.reminder_manager.cancel_reminder(reminder_id, user_id)
            if success:
                await update.message.reply_text("✅ Reminder cancelled successfully!")
            else:
                await update.message.reply_text(
                    "❌ Reminder not found or you don't have permission to cancel it."
                )
        except Exception as e:
            logger.error(f"Error cancelling reminder: {e}")
            await update.message.reply_text("❌ Invalid reminder ID format.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 I'm a reminder bot! Use /start to see available commands."
        )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Notify user about error
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )