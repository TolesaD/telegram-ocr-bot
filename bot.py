import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request
from config import Config
from database import ReminderManager
from handlers import CommandHandlers
from scheduler import ReminderScheduler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
application = None
scheduler = None

def setup_bot():
    global application, scheduler
    try:
        reminder_manager = ReminderManager()
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        handlers = CommandHandlers(reminder_manager)
        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("setreminder", handlers.set_reminder))
        application.add_handler(CommandHandler("viewreminders", handlers.view_reminders))
        application.add_handler(CommandHandler("cancelreminder", handlers.cancel_reminder))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        
        scheduler = ReminderScheduler(reminder_manager, application.bot)
        logger.info("✅ Bot setup completed")
        
    except Exception as e:
        logger.error(f"❌ Failed to setup bot: {e}")

async def setup_webhook():
    if Config.WEBHOOK_URL:
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"🌐 Webhook set to: {webhook_url}")

async def run_scheduler():
    if scheduler:
        await scheduler.start()

@app.route('/')
def index():
    return "🤖 Reminder Bot is Running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if application:
        update = request.get_json()
        asyncio.create_task(application.process_update(update))
    return 'ok'

@app.route('/health')
def health():
    return {'status': 'healthy'}

# Simple polling mode for local development
def run_polling():
    """Run bot in polling mode for local development"""
    try:
        reminder_manager = ReminderManager()
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        handlers = CommandHandlers(reminder_manager)
        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("setreminder", handlers.set_reminder))
        application.add_handler(CommandHandler("viewreminders", handlers.view_reminders))
        application.add_handler(CommandHandler("cancelreminder", handlers.cancel_reminder))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message))
        
        logger.info("🤖 Bot starting in polling mode...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    # For local development - use polling mode
    run_polling()