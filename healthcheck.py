#!/usr/bin/env python3
import os
import sys

def health_check():
    """Simple health check for Railway"""
    try:
        # Check if required environment variables are set
        required_vars = ['BOT_TOKEN']
        for var in required_vars:
            if not os.getenv(var):
                print(f"❌ Missing required environment variable: {var}")
                return 1
        
        # Check if we can import main dependencies
        try:
            import telegram
            import pytesseract
            from PIL import Image
            print("✅ All imports successful")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return 1
            
        print("✅ Health check passed")
        return 0
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())