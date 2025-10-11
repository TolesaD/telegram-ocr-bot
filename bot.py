import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import os
import threading
import asyncio
import queue

from config import Config
from models import db
from utils import format_currency, format_monthly_report, get_spending_tips, generate_text_visualization

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global application instance
application = None
update_queue = queue.Queue()

class ExpenseTrackerBot:
    def __init__(self):
        self.setup_handlers()
    
    def setup_handlers(self):
        global application
        application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        
        # Command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("addexpense", self.add_expense))
        application.add_handler(CommandHandler("report", self.monthly_report))
        application.add_handler(CommandHandler("budget", self.set_budget))
        application.add_handler(CommandHandler("tips", self.spending_tips))
        application.add_handler(CommandHandler("stats", self.expense_stats))
        
        # Callback query handlers
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors and send a friendly message."""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        if update and hasattr(update, 'effective_user'):
            try:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text="❌ Sorry, something went wrong. Please try again later."
                )
            except Exception:
                pass
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        if not db.get_user(user_id):
            db.create_user(user_id, user.username, user.first_name)
            await update.message.reply_text(f"👋 Welcome {user.first_name}! Your account has been created!")
        else:
            await update.message.reply_text(f"👋 Welcome back {user.first_name}!")
        
        welcome_text = f"""
💰 **Expense Tracker Bot**

I'll help you track your expenses and manage your finances effectively.

📋 **Available Commands:**
/addexpense - Log a new expense
/report - Get monthly expense report  
/budget - Set spending budgets
/tips - Get personalized saving tips
/stats - View your expense statistics
/help - Show this help message

💡 **Quick Start:** Use /addexpense to log your first expense!
        """
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Expense", callback_data="add_expense")],
            [InlineKeyboardButton("📊 Monthly Report", callback_data="monthly_report")],
            [InlineKeyboardButton("💰 Set Budget", callback_data="set_budget")],
            [InlineKeyboardButton("💡 Saving Tips", callback_data="saving_tips")],
            [InlineKeyboardButton("📈 View Stats", callback_data="view_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📋 **Expense Tracker Bot Commands:**

➕ **Add Expense**
/addexpense - Log a new expense with category

📊 **Reports & Analytics**  
/report - Generate monthly expense report
/stats - View your spending statistics

💰 **Budget Management**
/budget - Set monthly budgets for categories

💡 **Financial Tips**
/tips - Get personalized money saving tips

💡 Use the interactive buttons for quick access!
        """
        await update.message.reply_text(help_text)
    
    async def add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['awaiting_expense'] = True
        await update.message.reply_text(
            "💵 **Add Expense**\n\n"
            "Please enter your expense in this format:\n"
            "`Amount Category Description`\n\n"
            "**Example:** `50.00 Food Lunch at restaurant`\n\n"
            "Or choose a category below:",
            parse_mode='Markdown'
        )
        
        keyboard = []
        for i in range(0, len(Config.CATEGORIES), 2):
            row = []
            if i < len(Config.CATEGORIES):
                row.append(InlineKeyboardButton(Config.CATEGORIES[i], callback_data=f"category_{i}"))
            if i + 1 < len(Config.CATEGORIES):
                row.append(InlineKeyboardButton(Config.CATEGORIES[i + 1], callback_data=f"category_{i + 1}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📦 Select a category:", reply_markup=reply_markup)
    
    async def monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        now = datetime.now()
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        user = db.get_user(user_id)
        user_currency = user.get('currency', 'USD') if user else 'USD'
        
        report_text = format_monthly_report(expense_data, user_currency, now.month, now.year)
        await update.message.reply_text(report_text)
        
        if expense_data:
            viz_text = generate_text_visualization(expense_data, user_currency)
            await update.message.reply_text(viz_text)
    
    async def set_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user or not user.get('monthly_income'):
            context.user_data['awaiting_income'] = True
            await update.message.reply_text("💰 Enter monthly income:")
            return
        
        context.user_data['setting_budget'] = True
        await update.message.reply_text("📝 Enter: `Category Amount`\nExample: `Food 300`")
    
    async def spending_tips(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        now = datetime.now()
        user = db.get_user(user_id)
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        budgets = db.get_user_budgets(user_id)
        monthly_income = user.get('monthly_income', 0) if user else 0
        
        tips = get_spending_tips(expense_data, budgets, monthly_income)
        tips_text = "💡 **Tips**\n\n" + "\n".join(f"• {tip}" for tip in tips)
        await update.message.reply_text(tips_text)
    
    async def expense_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        expenses = db.get_user_expenses(user_id)
        
        if not expenses:
            await update.message.reply_text("📊 No expenses yet. Use /addexpense")
            return
        
        total = sum(e['amount'] for e in expenses)
        avg = total / len(expenses)
        max_exp = max(expenses, key=lambda x: x['amount'])
        
        stats_text = f"""📈 **Statistics**
💵 Total: {format_currency(total, user.get('currency', 'USD') if user else 'USD')}
📦 Count: {len(expenses)}
📊 Average: {format_currency(avg, user.get('currency', 'USD') if user else 'USD')}
💰 Largest: {format_currency(max_exp['amount'], user.get('currency', 'USD') if user else 'USD')} - {max_exp['category']}"""
        await update.message.reply_text(stats_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        
        if context.user_data.get('awaiting_income'):
            try:
                income = float(text)
                cursor = db.conn.cursor()
                cursor.execute('UPDATE users SET monthly_income = ? WHERE user_id = ?', (income, user_id))
                db.conn.commit()
                context.user_data['awaiting_income'] = False
                await update.message.reply_text(f"✅ Income set to {format_currency(income, 'USD')}")
            except ValueError:
                await update.message.reply_text("❌ Enter valid number")
        
        elif context.user_data.get('awaiting_expense'):
            parts = text.split(' ', 2)
            if len(parts) >= 2:
                try:
                    amount, category = float(parts[0]), parts[1]
                    desc = parts[2] if len(parts) > 2 else "No description"
                    if db.add_expense(user_id, amount, category, desc):
                        user = db.get_user(user_id)
                        curr = user.get('currency', 'USD') if user else 'USD'
                        await update.message.reply_text(f"✅ Added: {format_currency(amount, curr)} - {category}")
                    context.user_data['awaiting_expense'] = False
                except ValueError:
                    await update.message.reply_text("❌ Enter valid amount")
        
        elif context.user_data.get('setting_budget'):
            parts = text.split(' ', 1)
            if len(parts) == 2:
                try:
                    category, amount = parts[0], float(parts[1])
                    if db.set_budget(user_id, category, amount):
                        user = db.get_user(user_id)
                        curr = user.get('currency', 'USD') if user else 'USD'
                        await update.message.reply_text(f"✅ Budget: {category} - {format_currency(amount, curr)}")
                    context.user_data['setting_budget'] = False
                except ValueError:
                    await update.message.reply_text("❌ Enter valid amount")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        
        if data == "add_expense":
            context.user_data['awaiting_expense'] = True
            await query.edit_message_text("💵 Enter: `Amount Category Description`\nExample: `25.00 Food Lunch`")
        elif data == "monthly_report":
            user_id = query.from_user.id
            now = datetime.now()
            data = db.get_monthly_summary(user_id, now.month, now.year)
            user = db.get_user(user_id)
            currency = user.get('currency', 'USD') if user else 'USD'
            await query.edit_message_text(format_monthly_report(data, currency, now.month, now.year))
        elif data == "set_budget":
            user_id = query.from_user.id
            user = db.get_user(user_id)
            if not user or not user.get('monthly_income'):
                context.user_data['awaiting_income'] = True
                await query.edit_message_text("💰 Enter monthly income:")
            else:
                context.user_data['setting_budget'] = True
                await query.edit_message_text("📝 Enter: `Category Amount`\nExample: `Food 300`")
        elif data == "saving_tips":
            user_id = query.from_user.id
            now = datetime.now()
            user = db.get_user(user_id)
            data = db.get_monthly_summary(user_id, now.month, now.year)
            budgets = db.get_user_budgets(user_id)
            income = user.get('monthly_income', 0) if user else 0
            tips = get_spending_tips(data, budgets, income)
            await query.edit_message_text("💡 " + "\n".join(tips))
        elif data == "view_stats":
            user_id = query.from_user.id
            user = db.get_user(user_id)
            expenses = db.get_user_expenses(user_id)
            currency = user.get('currency', 'USD') if user else 'USD'
            
            if not expenses:
                await query.edit_message_text("📊 No expenses yet")
                return
            
            total = sum(e['amount'] for e in expenses)
            avg = total / len(expenses)
            max_exp = max(expenses, key=lambda x: x['amount'])
            
            text = f"""📈 **Statistics**
💵 Total: {format_currency(total, currency)}
📦 Count: {len(expenses)}
📊 Average: {format_currency(avg, currency)}
💰 Largest: {format_currency(max_exp['amount'], currency)} - {max_exp['category']}"""
            await query.edit_message_text(text)
        elif data.startswith("category_"):
            category_index = int(data.split("_")[1])
            category = Config.CATEGORIES[category_index]
            context.user_data['selected_category'] = category
            await query.edit_message_text(f"📦 {category}\nEnter: `Amount Description`\nExample: `50.00 Lunch`")

# Initialize the bot
bot = ExpenseTrackerBot()

# Flask app
from flask import Flask, request, jsonify

app = Flask(__name__)

# Process updates in background
def process_updates():
    """Process updates from the queue"""
    while True:
        try:
            update = update_queue.get(timeout=1)
            if update is None:  # Shutdown signal
                break
            asyncio.run_coroutine_threadsafe(
                application.process_update(update), 
                application._get_running_loop()
            )
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error processing update: {e}")

# Start update processor thread
processor_thread = threading.Thread(target=process_updates, daemon=True)
processor_thread.start()

@app.route('/')
def home():
    return "🤖 Expense Tracker Bot is running! Use /start in Telegram to begin."

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "expense-tracker-bot"})

@app.route(f'/{Config.TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram"""
    try:
        update_json = request.get_json()
        logger.info(f"📨 Received update from Telegram")
        
        # Create update object and add to queue
        update = Update.de_json(update_json, application.bot)
        update_queue.put(update)
        
        logger.info("✅ Update queued for processing")
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Initialize the application
def initialize_app():
    """Initialize the application"""
    try:
        # We don't need to run polling, just initialize
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.initialize())
        logger.info("✅ Application initialized for webhook mode")
    except Exception as e:
        logger.error(f"❌ Initialization error: {e}")

# Initialize when module loads
initialize_app()

if __name__ == '__main__':
    # Development mode
    application.run_polling()