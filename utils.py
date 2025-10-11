import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_expense_chart(expense_data, user_currency):
    """Placeholder for chart generation - returns None for SQLite version"""
    return None

def get_spending_tips(expense_data, budgets, monthly_income):
    tips = []
    
    if not expense_data:
        tips.append("📊 Start tracking your expenses to get personalized saving tips!")
        return tips
    
    total_spent = sum(item['total'] for item in expense_data)
    
    # Basic tips
    if monthly_income > 0:
        if total_spent > monthly_income * 0.9:
            tips.append("⚠️ You're spending over 90% of your income! Consider cutting back on non-essential expenses.")
        elif total_spent < monthly_income * 0.7:
            tips.append("✅ Great job! You're saving a good portion of your income.")
    
    # Category-specific tips
    for item in expense_data:
        if 'Food' in item['_id'] and monthly_income > 0 and item['total'] > monthly_income * 0.2:
            tips.append("🍽️ Your food expenses are high. Try meal planning and cooking at home more often.")
            break
    
    if not tips:
        tips.append("💡 You're doing well! Keep tracking your expenses to maintain good financial habits.")
    
    return tips[:3]

def format_currency(amount, currency):
    return f"{amount:.2f} {currency}"

def format_monthly_report(expense_data, user_currency, month, year):
    if not expense_data:
        return "📊 No expenses recorded for this month."
    
    total_spent = sum(item['total'] for item in expense_data)
    report = f"📊 Monthly Report for {month}/{year}\n\n"
    report += f"💵 Total Spent: {format_currency(total_spent, user_currency)}\n\n"
    report += "📦 Category Breakdown:\n"
    
    for item in expense_data:
        percentage = (item['total'] / total_spent * 100) if total_spent > 0 else 0
        report += f"{item['_id']}: {format_currency(item['total'], user_currency)} ({percentage:.1f}%)\n"
    
    return report

def generate_text_visualization(expense_data, user_currency):
    """Generate text-based visualization"""
    if not expense_data:
        return ""
    
    total_spent = sum(item['total'] for item in expense_data)
    viz_text = "📈 Visual Breakdown:\n\n"
    
    for item in expense_data:
        percentage = (item['total'] / total_spent * 100) if total_spent > 0 else 0
        bar_length = int(percentage / 3)  # Each █ represents 3%
        bar = "█" * bar_length
        viz_text += f"{item['_id']}\n"
        viz_text += f"{bar} {percentage:.1f}%\n\n"
    
    return viz_text