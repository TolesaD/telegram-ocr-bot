import logging
import asyncio
from telegram.ext import Application
from flask import Flask, request
import threading
import time

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables
application = None
scheduler = None

def setup_bot():
    """Setup bot components"""
    global application, scheduler
    
    try:
        from config import Config
        from database import ReminderManager
        from handlers import CommandHandlers
        from scheduler import ReminderScheduler
        
        # Initialize components
        reminder_manager = ReminderManager()
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Setup handlers
        handlers = CommandHandlers(reminder_manager)
        
        # Add handlers to application
        application.add_handler(handlers.start)
        application.add_handler(handlers.set_reminder)
        application.add_handler(handlers.view_reminders)
        application.add_handler(handlers.cancel_reminder)
        application.add_handler(handlers.handle_message)
        application.add_error_handler(handlers.error_handler)
        
        # Setup scheduler
        scheduler = ReminderScheduler(reminder_manager, application.bot)
        
        logger.info("Bot setup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup bot: {e}")

def run_bot():
    """Run bot in background thread"""
    global application, scheduler
    
    try:
        from config import Config
        
        if application is None:
            setup_bot()
        
        # Set webhook
        webhook_url = f"{Config.WEBHOOK_URL}/webhook"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def setup():
            await application.initialize()
            await application.start()
            await application.bot.set_webhook(webhook_url)
            logger.info(f"Webhook set to: {webhook_url}")
            
            # Start scheduler
            await scheduler.start()
        
        loop.run_until_complete(setup())
        logger.info("Bot is running with webhook")
        
    except Exception as e:
        logger.error(f"Error running bot: {e}")

# Start bot when module loads
try:
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot startup initiated")
except Exception as e:
    logger.error(f"Failed to start bot thread: {e}")

@app.route('/')
def index():
    return """
    <h1>🤖 Reminder Bot is Running!</h1>
    <p>Your Telegram reminder bot is active and ready to receive messages.</p>
    <p>Visit your bot on Telegram to start setting reminders.</p>
    <hr>
    <p>Status: ✅ Operational</p>
    <p>Check the logs for any issues.</p>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates from Telegram"""
    global application
    
    if application is None:
        return 'Bot not initialized', 503
    
    try:
        update = request.get_json()
        logger.info(f"Received update: {update}")
        
        # Process update in background
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process_update():
            await application.process_update(update)
        
        loop.run_until_complete(process_update())
        return 'ok'
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return 'error', 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': time.time()}

@app.route('/restart')
def restart_bot():
    """Manual restart endpoint (use carefully)"""
    try:
        global application, scheduler
        application = None
        scheduler = None
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        return "Bot restart initiated"
    except Exception as e:
        return f"Restart failed: {e}", 500

# For local development
if __name__ == '__main__':
    setup_bot()
    app.run(host='0.0.0.0', port=5000, debug=False)