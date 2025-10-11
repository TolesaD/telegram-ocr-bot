#!/usr/bin/env python3
"""
Test database connection
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from models import db
from config import Config

print("🔧 Testing database connection...")

try:
    # Test connection
    if hasattr(db, 'use_sqlite') and db.use_sqlite:
        print("✅ Using SQLite database (MongoDB fallback)")
    else:
        print("✅ Using MongoDB Atlas")
    
    # Test basic operations
    test_user_id = 99999  # Use a test ID
    db.create_user(test_user_id, "test_user", "Test User")
    print("✅ User creation test passed")
    
    db.add_expense(test_user_id, 25.50, "Food", "Test expense")
    print("✅ Expense addition test passed")
    
    expenses = db.get_user_expenses(test_user_id)
    print(f"✅ Retrieved {len(expenses)} expenses")
    
    db.set_budget(test_user_id, "Food", 300)
    print("✅ Budget setting test passed")
    
    budgets = db.get_user_budgets(test_user_id)
    print(f"✅ Retrieved {len(budgets)} budgets")
    
    summary = db.get_monthly_summary(test_user_id, 10, 2025)
    print(f"✅ Monthly summary test passed: {len(summary)} categories")
    
    print("\n🎉 All database tests passed!")
    
except Exception as e:
    print(f"❌ Database test failed: {e}")
    sys.exit(1)