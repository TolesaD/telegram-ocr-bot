#!/usr/bin/env python3
"""
Test script to verify all imports work
"""
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

def test_imports():
    print("Testing imports...")
    
    try:
        # Test basic imports
        from telegram import Update
        from telegram.ext import Application, CommandHandler
        print("✅ telegram imports work")
    except ImportError as e:
        print(f"❌ telegram import failed: {e}")
        return False
    
    try:
        # Test config
        import config
        print("✅ config import works")
    except ImportError as e:
        print(f"❌ config import failed: {e}")
        # Try alternative
        try:
            import config_optimized as config
            print("✅ config_optimized import works")
        except ImportError as e2:
            print(f"❌ config_optimized import failed: {e2}")
            return False
    
    try:
        # Test database
        from database.mongodb import db
        print("✅ database import works")
    except ImportError as e:
        print(f"❌ database import failed: {e}")
        return False
    
    try:
        # Test handlers
        from handlers.start import start_command
        from handlers.ocr import handle_image
        from handlers.menu import show_main_menu
        print("✅ handler imports work")
    except ImportError as e:
        print(f"❌ handler imports failed: {e}")
        return False
    
    try:
        # Test utils
        from utils.image_processing import ocr_processor
        from utils.text_formatter import TextFormatter
        print("✅ utils imports work")
    except ImportError as e:
        print(f"❌ utils imports failed: {e}")
        return False
    
    print("🎉 All imports successful! Bot should work now.")
    return True

if __name__ == '__main__':
    test_imports()