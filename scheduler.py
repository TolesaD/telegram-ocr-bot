import asyncio
import logging
from datetime import datetime
from telegram import Bot
from config import Config

logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self, reminder_manager, bot):
        self.reminder_manager = reminder_manager
        self.bot = bot
        self.is_running = False
    
    async def start(self):
        self.is_running = True
        logger.info("⏰ Reminder scheduler started")
        
        while self.is_running:
            try:
                await self.check_reminders()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(60)
    
    async def stop(self):
        self.is_running = False
    
    async def check_reminders(self):
        due_reminders = self.reminder_manager.get_due_reminders()
        
        for reminder in due_reminders:
            try:
                recurrence_text = f" ({reminder['recurrence']})" if reminder['recurrence'] else ""
                message_text = (
                    f"🔔 Reminder{recurrence_text}\n"
                    f"⏰ {reminder['time']}\n"
                    f"📝 {reminder['message']}"
                )
                
                await self.bot.send_message(
                    chat_id=reminder['chat_id'],
                    text=message_text
                )
                
                if reminder['recurrence']:
                    self.reminder_manager.update_next_reminder(str(reminder['_id']))
                else:
                    self.reminder_manager.cancel_reminder(str(reminder['_id']), reminder['user_id'])
                
                logger.info(f"Sent reminder to user {reminder['user_id']}")
                
            except Exception as e:
                logger.error(f"Failed to send reminder: {e}")
                if "chat not found" in str(e).lower() or "blocked" in str(e).lower():
                    self.reminder_manager.cancel_reminder(str(reminder['_id']), reminder['user_id'])