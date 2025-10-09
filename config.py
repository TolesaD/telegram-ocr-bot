import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    MONGODB_URI = os.getenv('MONGODB_URI')
    DATABASE_NAME = 'expense_tracker'
    
    # Expense categories
    CATEGORIES = [
        '🍔 Food & Dining',
        '🏠 Housing',
        '🚗 Transportation',
        '🛒 Shopping',
        '💊 Healthcare',
        '🎯 Entertainment',
        '📚 Education',
        '✈️ Travel',
        '💡 Utilities',
        '💰 Savings',
        '📱 Technology',
        '🎁 Gifts',
        '🏋️ Fitness',
        '🐾 Pets',
        '📊 Other'
    ]
    
    # Budget recommendations based on income
    BUDGET_RECOMMENDATIONS = {
        '🍔 Food & Dining': 0.15,
        '🏠 Housing': 0.25,
        '🚗 Transportation': 0.15,
        '🛒 Shopping': 0.10,
        '💊 Healthcare': 0.05,
        '🎯 Entertainment': 0.05,
        '📚 Education': 0.05,
        '✈️ Travel': 0.05,
        '💡 Utilities': 0.08,
        '💰 Savings': 0.12
    }