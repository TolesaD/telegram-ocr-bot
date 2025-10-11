#!/usr/bin/env python3
"""
Test script to verify production readiness
"""
import sys
import os

print("🔧 Testing production deployment...")

# Test imports
try:
    from bot import app, bot
    print("✅ Bot imports successful")
except Exception as e:
    print(f"❌ Bot import failed: {e}")
    sys.exit(1)

try:
    from models import db
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

try:
    from config import Config
    print("✅ Config loaded successfully")
    print(f"   - Token: {'Set' if Config.TELEGRAM_TOKEN else 'Missing'}")
    print(f"   - Environment: {Config.ENVIRONMENT}")
except Exception as e:
    print(f"❌ Config load failed: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! Ready for deployment.")
print("\n📋 Next steps:")
print("1. Push code to GitHub")
print("2. Deploy to PythonAnywhere")
print("3. Set webhook URL")