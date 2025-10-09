import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
import io
from config import Config

def generate_expense_chart(expense_data, user_currency):
    if not expense_data:
        return None
    
    categories = [item['_id'] for item in expense_data]
    amounts = [item['total'] for item in expense_data]
    
    plt.figure(figsize=(10, 8))
    colors = sns.color_palette('husl', len(categories))
    
    # Create pie chart
    plt.subplot(1, 2, 1)
    plt.pie(amounts, labels=categories, autopct='%1.1f%%', colors=colors)
    plt.title('Expense Distribution')
    
    # Create bar chart
    plt.subplot(1, 2, 2)
    plt.barh(categories, amounts, color=colors)
    plt.xlabel(f'Amount ({user_currency})')
    plt.title('Expenses by Category')
    plt.tight_layout()
    
    # Save to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def get_spending_tips(expense_data, budgets, monthly_income):
    tips = []
    
    if not expense_data:
        tips.append("📊 Start tracking your expenses to get personalized saving tips!")
        return tips
    
    total_spent = sum(item['total'] for item in expense_data)
    
    # Calculate percentages
    category_percentages = {}
    for item in expense_data:
        percentage = (item['total'] / monthly_income * 100) if monthly_income > 0 else 0
        category_percentages[item['_id']] = percentage
    
    # Generate tips based on spending patterns
    if total_spent > monthly_income * 0.9 and monthly_income > 0:
        tips.append("⚠️ You're spending over 90% of your income! Consider cutting back on non-essential expenses.")
    
    food_spent = next((item for item in expense_data if 'Food' in item['_id']), None)
    if food_spent and food_spent['total'] > monthly_income * 0.2:
        tips.append("🍽️ Your food expenses are high. Try meal planning and cooking at home more often.")
    
    entertainment_spent = next((item for item in expense_data if 'Entertainment' in item['_id']), None)
    if entertainment_spent and entertainment_spent['total'] > monthly_income * 0.1:
        tips.append("🎬 Consider free entertainment options like parks, libraries, or community events.")
    
    shopping_spent = next((item for item in expense_data if 'Shopping' in item['_id']), None)
    if shopping_spent and shopping_spent['total'] > monthly_income * 0.15:
        tips.append("🛍️ Implement a 24-hour waiting rule before making non-essential purchases.")
    
    if total_spent < monthly_income * 0.7 and monthly_income > 0:
        tips.append("✅ Great job! You're saving a good portion of your income. Consider investing the surplus.")
    
    # Budget comparison tips
    for budget in budgets:
        actual_spent = next((item for item in expense_data if item['_id'] == budget['category']), None)
        if actual_spent and actual_spent['total'] > budget['amount']:
            tips.append(f"📈 You've exceeded your {budget['category']} budget. Review your spending in this category.")
    
    if not tips:
        tips.append("💡 You're doing well! Keep tracking your expenses to maintain good financial habits.")
    
    return tips[:5]  # Return max 5 tips

def format_currency(amount, currency):
    return f"{amount:.2f} {currency}"

def format_monthly_report(expense_data, user_currency, month, year):
    if not expense_data:
        return "No expenses recorded for this month."
    
    total_spent = sum(item['total'] for item in expense_data)
    report = f"📊 Monthly Report for {month}/{year}\n\n"
    report += f"Total Spent: {format_currency(total_spent, user_currency)}\n\n"
    report += "Category Breakdown:\n"
    
    for item in expense_data:
        percentage = (item['total'] / total_spent * 100) if total_spent > 0 else 0
        report += f"{item['_id']}: {format_currency(item['total'], user_currency)} ({percentage:.1f}%)\n"
    
    return report