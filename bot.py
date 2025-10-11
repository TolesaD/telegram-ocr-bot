import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import os
import threading
import asyncio

from config import Config
from models import db
from utils import generate_expense_chart, get_spending_tips, format_currency, format_monthly_report, generate_text_visualization

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ExpenseTrackerBot:
    def __init__(self):
        self.application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("addexpense", self.add_expense))
        self.application.add_handler(CommandHandler("report", self.monthly_report))
        self.application.add_handler(CommandHandler("budget", self.set_budget))
        self.application.add_handler(CommandHandler("tips", self.spending_tips))
        self.application.add_handler(CommandHandler("stats", self.expense_stats))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors and send a friendly message."""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        # Send a message to the user
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
        
        # Check if user exists, if not create
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
        
        # Show category buttons
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
        
        # Add text visualization
        if expense_data:
            viz_text = generate_text_visualization(expense_data, user_currency)
            await update.message.reply_text(viz_text)
    
    async def set_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user or not user.get('monthly_income'):
            context.user_data['awaiting_income'] = True
            await update.message.reply_text(
                "💰 **Set Monthly Income**\n\n"
                "First, let's set your monthly income. Please enter your monthly income:\n\n"
                "**Example:** `3000`"
            )
            return
        
        context.user_data['setting_budget'] = True
        await update.message.reply_text(
            f"📝 **Set Budget**\n\n"
            f"Your monthly income: {format_currency(user['monthly_income'], user.get('currency', 'USD'))}\n\n"
            "Please enter budget in format:\n"
            "`Category Amount`\n\n"
            "**Example:** `Food 300`"
        )
    
    async def spending_tips(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        now = datetime.now()
        user = db.get_user(user_id)
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        budgets = db.get_user_budgets(user_id)
        monthly_income = user.get('monthly_income', 0) if user else 0
        
        tips = get_spending_tips(expense_data, budgets, monthly_income)
        
        tips_text = "💡 **Personalized Saving Tips**\n\n"
        for i, tip in enumerate(tips, 1):
            tips_text += f"{i}. {tip}\n\n"
        
        await update.message.reply_text(tips_text)
    
    async def expense_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        expenses = db.get_user_expenses(user_id)
        
        if not expenses:
            await update.message.reply_text("📊 No expenses recorded yet. Start by adding your first expense using /addexpense!")
            return
        
        total_spent = sum(expense['amount'] for expense in expenses)
        avg_expense = total_spent / len(expenses)
        most_expensive = max(expenses, key=lambda x: x['amount'])
        
        stats_text = f"""
📈 **Your Expense Statistics**

💵 Total Spent: {format_currency(total_spent, user.get('currency', 'USD') if user else 'USD')}
📦 Total Expenses: {len(expenses)}
📊 Average Expense: {format_currency(avg_expense, user.get('currency', 'USD') if user else 'USD')}
💰 Most Expensive: {format_currency(most_expensive['amount'], user.get('currency', 'USD') if user else 'USD')} - {most_expensive['category']}
        """
        
        await update.message.reply_text(stats_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        
        if context.user_data.get('awaiting_income'):
            try:
                income = float(text)
                # Update user income
                user = db.get_user(user_id)
                if user:
                    cursor = db.conn.cursor()
                    cursor.execute('UPDATE users SET monthly_income = ? WHERE user_id = ?', (income, user_id))
                    db.conn.commit()
                
                context.user_data['awaiting_income'] = False
                await update.message.reply_text(
                    f"✅ Monthly income set to {format_currency(income, 'USD')}!\n\n"
                    "Now let's set up your budgets. Use /budget to continue."
                )
            except ValueError:
                await update.message.reply_text("❌ Please enter a valid number for income.")
        
        elif context.user_data.get('awaiting_expense'):
            await self.process_expense_input(update, context, text)
        
        elif context.user_data.get('setting_budget'):
            await self.process_budget_input(update, context, text)
    
    async def process_expense_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        user_id = update.effective_user.id
        
        # Simple parsing: amount category description
        parts = text.split(' ', 2)
        if len(parts) < 2:
            await update.message.reply_text("❌ Please use format: Amount Category Description")
            return
        
        try:
            amount = float(parts[0])
            category = parts[1]
            description = parts[2] if len(parts) > 2 else "No description"
            
            # Validate category
            valid_categories = [cat.split(' ', 1)[-1] for cat in Config.CATEGORIES]
            if category not in valid_categories:
                await update.message.reply_text("❌ Invalid category. Please use one of the provided categories.")
                return
            
            success = db.add_expense(user_id, amount, category, description)
            context.user_data['awaiting_expense'] = False
            
            if success:
                user = db.get_user(user_id)
                await update.message.reply_text(
                    f"✅ **Expense Added Successfully!**\n\n"
                    f"💵 Amount: {format_currency(amount, user.get('currency', 'USD') if user else 'USD')}\n"
                    f"📦 Category: {category}\n"
                    f"📝 Description: {description}\n\n"
                    f"Use /report to see your spending summary!"
                )
            else:
                await update.message.reply_text("❌ Error adding expense. Please try again.")
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid amount.")
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            await update.message.reply_text("❌ Error adding expense. Please try again.")
    
    async def process_budget_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        user_id = update.effective_user.id
        parts = text.split(' ', 1)
        
        if len(parts) < 2:
            await update.message.reply_text("❌ Please use format: Category Amount")
            return
        
        category = parts[0]
        try:
            amount = float(parts[1])
            success = db.set_budget(user_id, category, amount)
            
            if success:
                user = db.get_user(user_id)
                await update.message.reply_text(
                    f"✅ **Budget Set Successfully!**\n\n"
                    f"📦 Category: {category}\n"
                    f"💰 Amount: {format_currency(amount, user.get('currency', 'USD') if user else 'USD')}"
                )
            else:
                await update.message.reply_text("❌ Error setting budget. Please try again.")
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid amount.")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data == "add_expense":
            await self.add_expense_callback(query, context)
        elif data == "monthly_report":
            await self.monthly_report_callback(query, context)
        elif data == "set_budget":
            await self.set_budget_callback(query, context)
        elif data == "saving_tips":
            await self.spending_tips_callback(query, context)
        elif data == "view_stats":
            await self.expense_stats_callback(query, context)
        elif data.startswith("category_"):
            await self.category_selection(query, context, data)
    
    async def add_expense_callback(self, query, context):
        context.user_data['awaiting_expense'] = True
        await query.edit_message_text(
            "💵 **Add Expense**\n\n"
            "Please enter your expense in this format:\n"
            "`Amount Category Description`\n\n"
            "**Example:** `50.00 Food Lunch at restaurant`"
        )
    
    async def monthly_report_callback(self, query, context):
        user_id = query.from_user.id
        now = datetime.now()
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        user = db.get_user(user_id)
        user_currency = user.get('currency', 'USD') if user else 'USD'
        
        report_text = format_monthly_report(expense_data, user_currency, now.month, now.year)
        await query.edit_message_text(report_text)
        
        if expense_data:
            viz_text = generate_text_visualization(expense_data, user_currency)
            await context.bot.send_message(chat_id=query.message.chat_id, text=viz_text)
    
    async def set_budget_callback(self, query, context):
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user or not user.get('monthly_income'):
            context.user_data['awaiting_income'] = True
            await query.edit_message_text(
                "💰 **Set Monthly Income**\n\n"
                "First, let's set your monthly income. Please enter your monthly income:\n\n"
                "**Example:** `3000`"
            )
            return
        
        context.user_data['setting_budget'] = True
        await query.edit_message_text(
            f"📝 **Set Budget**\n\n"
            f"Your monthly income: {format_currency(user['monthly_income'], user.get('currency', 'USD'))}\n\n"
            "Please enter budget in format:\n"
            "`Category Amount`\n\n"
            "**Example:** `Food 300`"
        )
    
    async def spending_tips_callback(self, query, context):
        user_id = query.from_user.id
        now = datetime.now()
        user = db.get_user(user_id)
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        budgets = db.get_user_budgets(user_id)
        monthly_income = user.get('monthly_income', 0) if user else 0
        
        tips = get_spending_tips(expense_data, budgets, monthly_income)
        
        tips_text = "💡 **Personalized Saving Tips**\n\n"
        for i, tip in enumerate(tips, 1):
            tips_text += f"{i}. {tip}\n\n"
        
        await query.edit_message_text(tips_text)
    
    async def expense_stats_callback(self, query, context):
        user_id = query.from_user.id
        user = db.get_user(user_id)
        expenses = db.get_user_expenses(user_id)
        
        if not expenses:
            await query.edit_message_text("📊 No expenses recorded yet. Start by adding your first expense using /addexpense!")
            return
        
        total_spent = sum(expense['amount'] for expense in expenses)
        avg_expense = total_spent / len(expenses)
        most_expensive = max(expenses, key=lambda x: x['amount'])
        
        stats_text = f"""
📈 **Your Expense Statistics**

💵 Total Spent: {format_currency(total_spent, user.get('currency', 'USD') if user else 'USD')}
📦 Total Expenses: {len(expenses)}
📊 Average Expense: {format_currency(avg_expense, user.get('currency', 'USD') if user else 'USD')}
💰 Most Expensive: {format_currency(most_expensive['amount'], user.get('currency', 'USD') if user else 'USD')} - {most_expensive['category']}
        """
        
        await query.edit_message_text(stats_text)
    
    async def category_selection(self, query, context, data):
        category_index = int(data.split("_")[1])
        category = Config.CATEGORIES[category_index]
        context.user_data['selected_category'] = category
        await query.edit_message_text(
            f"📦 Selected category: {category}\n\n"
            "Now please enter the amount and description:\n"
            "`Amount Description`\n\n"
            "**Example:** `50.00 Lunch at restaurant`"
        )

# Initialize the bot
bot = ExpenseTrackerBot()

# Flask app for production
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global variable to track bot initialization
bot_initialized = False

def initialize_bot():
    """Initialize the bot application"""
    global bot_initialized
    try:
        # Initialize the bot application
        import asyncio
        
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize the application
        loop.run_until_complete(bot.application.initialize())
        bot_initialized = True
        logger.info("✅ Bot application initialized successfully for webhook mode!")
        
    except Exception as e:
        logger.error(f"❌ Bot initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Initialize bot when Flask starts
@app.before_first_request
def before_first_request():
    if not bot_initialized:
        logger.info("🚀 Initializing bot application...")
        init_thread = threading.Thread(target=initialize_bot, daemon=True)
        init_thread.start()

@app.route('/')
def home():
    return "🤖 Expense Tracker Bot is running! Use /start in Telegram to begin."

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy", 
        "service": "expense-tracker-bot", 
        "bot_initialized": bot_initialized
    })

@app.route(f'/{Config.TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram"""
    try:
        if not bot_initialized:
            logger.warning("⚠️ Bot not initialized yet, initializing now...")
            initialize_bot()
            
        update_json = request.get_json()
        logger.info(f"📨 Received webhook update")
        
        # Properly process the update
        update = Update.de_json(update_json, bot.application.bot)
        bot.application.update_queue.put(update)
        
        logger.info("✅ Update queued for processing")
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

# Initialize bot when module is imported
logger.info("🔧 Starting bot initialization...")
initialize_bot()

# Development mode
if __name__ == '__main__':
    # For development - use polling
    print("🔧 Starting in development mode (polling)...")
    bot.application.run_polling()