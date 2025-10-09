import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import re
import os

from config import Config
from models import Database
from utils import generate_expense_chart, get_spending_tips, format_currency, format_monthly_report

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        # Check if user exists, if not create
        if not db.get_user(user_id):
            db.create_user(user_id, user.username, user.first_name)
        
        welcome_text = f"""
👋 Welcome {user.first_name} to Expense Tracker Bot!

I'll help you track your expenses and manage your finances effectively.

📋 **Available Commands:**
/add_expense - Log a new expense
/report - Get monthly expense report
/budget - Set spending budgets
/tips - Get personalized saving tips
/stats - View your expense statistics
/help - Show this help message

💡 **Pro Tip:** Use the buttons below for quick access to common features!
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

🛠️ **Settings**
/help - Show this help message

💡 You can also use the interactive buttons for quick access!
        """
        await update.message.reply_text(help_text)
    
    async def add_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['awaiting_expense'] = True
        await update.message.reply_text(
            "💵 Please enter your expense in the format:\n"
            "`Amount Category Description`\n\n"
            "Example: `50.00 Food Lunch at restaurant`\n\n"
            "Or choose a category:",
            parse_mode='Markdown'
        )
        
        # Show category buttons
        keyboard = []
        categories = [cat.split(' ', 1)[-1] for cat in Config.CATEGORIES]
        for i in range(0, len(categories), 2):
            row = []
            if i < len(categories):
                row.append(InlineKeyboardButton(Config.CATEGORIES[i], callback_data=f"category_{i}"))
            if i + 1 < len(categories):
                row.append(InlineKeyboardButton(Config.CATEGORIES[i + 1], callback_data=f"category_{i + 1}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select a category:", reply_markup=reply_markup)
    
    async def monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        now = datetime.now()
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        user = db.get_user(user_id)
        user_currency = user.get('currency', 'USD')
        
        report_text = format_monthly_report(expense_data, user_currency, now.month, now.year)
        
        # Generate chart
        chart = generate_expense_chart(expense_data, user_currency)
        
        if chart:
            await update.message.reply_photo(
                photo=chart,
                caption=report_text
            )
        else:
            await update.message.reply_text(report_text)
    
    async def set_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        
        if not user.get('monthly_income'):
            context.user_data['awaiting_income'] = True
            await update.message.reply_text(
                "💰 First, let's set your monthly income. Please enter your monthly income:"
            )
            return
        
        context.user_data['setting_budget'] = True
        await update.message.reply_text(
            f"📝 Setting budget for categories. Your monthly income: {format_currency(user['monthly_income'], user.get('currency', 'USD'))}\n\n"
            "Please enter budget in format:\n"
            "`Category Amount`\n\n"
            "Example: `Food 300`"
        )
        
        # Show quick budget setup based on recommendations
        keyboard = []
        for category, percentage in Config.BUDGET_RECOMMENDATIONS.items():
            recommended_amount = user['monthly_income'] * percentage
            keyboard.append([
                InlineKeyboardButton(
                    f"{category}: {format_currency(recommended_amount, user.get('currency', 'USD'))}",
                    callback_data=f"quick_budget_{category}_{recommended_amount}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🎯 Set All Recommended", callback_data="set_all_budgets")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("💡 Quick budget setup (based on financial recommendations):", reply_markup=reply_markup)
    
    async def spending_tips(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        now = datetime.now()
        user = db.get_user(user_id)
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        budgets = db.get_user_budgets(user_id)
        monthly_income = user.get('monthly_income', 0)
        
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
            await update.message.reply_text("No expenses recorded yet. Start by adding your first expense!")
            return
        
        total_spent = sum(expense['amount'] for expense in expenses)
        avg_expense = total_spent / len(expenses)
        most_expensive = max(expenses, key=lambda x: x['amount'])
        
        stats_text = f"""
📈 **Your Expense Statistics**

💵 Total Spent: {format_currency(total_spent, user.get('currency', 'USD'))}
📦 Total Expenses: {len(expenses)}
📊 Average Expense: {format_currency(avg_expense, user.get('currency', 'USD'))}
💰 Most Expensive: {format_currency(most_expensive['amount'], user.get('currency', 'USD'))} - {most_expensive['category']}

🎯 Keep tracking to see more detailed insights!
        """
        
        await update.message.reply_text(stats_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        
        if context.user_data.get('awaiting_income'):
            try:
                income = float(text)
                db.users.update_one(
                    {'user_id': user_id},
                    {'$set': {'monthly_income': income}}
                )
                context.user_data['awaiting_income'] = False
                await update.message.reply_text(
                    f"✅ Monthly income set to {format_currency(income, 'USD')}!\n"
                    "Now let's set up your budgets."
                )
                await self.set_budget(update, context)
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
            
            db.add_expense(user_id, amount, category, description)
            context.user_data['awaiting_expense'] = False
            
            user = db.get_user(user_id)
            await update.message.reply_text(
                f"✅ Expense added!\n"
                f"💵 Amount: {format_currency(amount, user.get('currency', 'USD'))}\n"
                f"📦 Category: {category}\n"
                f"📝 Description: {description}"
            )
            
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
            db.set_budget(user_id, category, amount)
            
            user = db.get_user(user_id)
            await update.message.reply_text(
                f"✅ Budget set!\n"
                f"📦 Category: {category}\n"
                f"💰 Amount: {format_currency(amount, user.get('currency', 'USD'))}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid amount.")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data == "add_expense":
            context.user_data['awaiting_expense'] = True
            await query.edit_message_text(
                "💵 Please enter your expense in the format:\n"
                "`Amount Category Description`\n\n"
                "Example: `50.00 Food Lunch at restaurant`"
            )
        
        elif data == "monthly_report":
            await self.monthly_report_callback(query, context)
        
        elif data == "set_budget":
            await self.set_budget_callback(query, context)
        
        elif data == "saving_tips":
            await self.spending_tips_callback(query, context)
        
        elif data == "view_stats":
            await self.expense_stats_callback(query, context)
        
        elif data.startswith("category_"):
            category_index = int(data.split("_")[1])
            category = Config.CATEGORIES[category_index]
            context.user_data['selected_category'] = category
            await query.edit_message_text(
                f"Selected category: {category}\n"
                "Now please enter the amount and description:\n"
                "`Amount Description`\n\n"
                "Example: `50.00 Lunch at restaurant`"
            )
        
        elif data.startswith("quick_budget_"):
            parts = data.split('_')
            category = ' '.join(parts[2:-1])
            amount = float(parts[-1])
            
            db.set_budget(user_id, category, amount)
            user = db.get_user(user_id)
            
            await query.edit_message_text(
                f"✅ Budget set for {category}: {format_currency(amount, user.get('currency', 'USD'))}"
            )
        
        elif data == "set_all_budgets":
            user = db.get_user(user_id)
            monthly_income = user.get('monthly_income', 0)
            
            for category, percentage in Config.BUDGET_RECOMMENDATIONS.items():
                amount = monthly_income * percentage
                db.set_budget(user_id, category, amount)
            
            await query.edit_message_text(
                "✅ All recommended budgets have been set based on your income!"
            )
    
    async def monthly_report_callback(self, query, context):
        user_id = query.from_user.id
        now = datetime.now()
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        user = db.get_user(user_id)
        user_currency = user.get('currency', 'USD')
        
        report_text = format_monthly_report(expense_data, user_currency, now.month, now.year)
        
        chart = generate_expense_chart(expense_data, user_currency)
        
        if chart:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=chart,
                caption=report_text
            )
        else:
            await query.edit_message_text(report_text)
    
    async def set_budget_callback(self, query, context):
        user_id = query.from_user.id
        user = db.get_user(user_id)
        
        if not user.get('monthly_income'):
            context.user_data['awaiting_income'] = True
            await query.edit_message_text(
                "💰 First, let's set your monthly income. Please enter your monthly income:"
            )
            return
        
        context.user_data['setting_budget'] = True
        await query.edit_message_text(
            f"📝 Setting budget for categories. Your monthly income: {format_currency(user['monthly_income'], user.get('currency', 'USD'))}\n\n"
            "Please enter budget in format:\n"
            "`Category Amount`\n\n"
            "Example: `Food 300`"
        )
    
    async def spending_tips_callback(self, query, context):
        user_id = query.from_user.id
        now = datetime.now()
        user = db.get_user(user_id)
        
        expense_data = db.get_monthly_summary(user_id, now.month, now.year)
        budgets = db.get_user_budgets(user_id)
        monthly_income = user.get('monthly_income', 0)
        
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
            await query.edit_message_text("No expenses recorded yet. Start by adding your first expense!")
            return
        
        total_spent = sum(expense['amount'] for expense in expenses)
        avg_expense = total_spent / len(expenses)
        most_expensive = max(expenses, key=lambda x: x['amount'])
        
        stats_text = f"""
📈 **Your Expense Statistics**

💵 Total Spent: {format_currency(total_spent, user.get('currency', 'USD'))}
📦 Total Expenses: {len(expenses)}
📊 Average Expense: {format_currency(avg_expense, user.get('currency', 'USD'))}
💰 Most Expensive: {format_currency(most_expensive['amount'], user.get('currency', 'USD'))} - {most_expensive['category']}

🎯 Keep tracking to see more detailed insights!
        """
        
        await query.edit_message_text(stats_text)

    # Webhook methods
    async def webhook_handler(self, update_dict):
        """Handle webhook updates"""
        update = Update.de_json(update_dict, self.application.bot)
        await self.application.process_update(update)

    def run_webhook(self, webhook_url, port=8000):
        """Run the bot with webhook"""
        # Set webhook
        self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=Config.TELEGRAM_TOKEN,
            webhook_url=f"{webhook_url}/{Config.TELEGRAM_TOKEN}",
            secret_token=None
        )

    def run_polling(self):
        """Run the bot with polling (for development)"""
        self.application.run_polling()

# Flask app for webhook
from flask import Flask, request, jsonify

app = Flask(__name__)
bot = ExpenseTrackerBot()

@app.route('/')
def home():
    return "Expense Tracker Bot is running!"

@app.route(f'/{Config.TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram"""
    update = request.get_json()
    bot.application.update_queue.put(update)
    return jsonify({"status": "ok"})

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Manually set webhook URL"""
    webhook_url = request.args.get('url')
    if webhook_url:
        bot.application.bot.set_webhook(f"{webhook_url}/{Config.TELEGRAM_TOKEN}")
        return jsonify({"status": "webhook set", "url": webhook_url})
    return jsonify({"error": "No URL provided"})

if __name__ == '__main__':
    # For development, use polling
    if os.environ.get('ENVIRONMENT') == 'production':
        # In production, this will be run by gunicorn
        pass
    else:
        # Development - use polling
        print("Starting bot in development mode (polling)...")
        bot.run_polling()