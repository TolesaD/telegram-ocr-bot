import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8452300221:AAHj8GaG_hE5OLaQslUl2I8b1rW8zCqYWG4')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Expense categories
    CATEGORIES = [
        '🍔 Food',
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
        '🍔 Food': 0.15,
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