#!/usr/bin/env python3
"""
Setup script for PythonAnywhere
Run this in your PythonAnywhere console
"""
import os
import subprocess
import sys

def setup_pythonanywhere():
    print("🚀 Setting up Tesseract on PythonAnywhere...")
    
    # Check if we're on PythonAnywhere
    if 'PYTHONANYWHERE_DOMAIN' not in os.environ:
        print("❌ This script is for PythonAnywhere only!")
        return
    
    print("📍 Platform: PythonAnywhere detected")
    
    # Test Tesseract installation
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Tesseract is installed:")
            print(result.stdout)
        else:
            print("❌ Tesseract not working properly")
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
        print("💡 Run these commands in Bash console:")
        print("apt-get update")
        print("apt-get install -y tesseract-ocr")
        print("apt-get install -y tesseract-ocr-eng tesseract-ocr-spa tesseract-ocr-fra")
        print("apt-get install -y tesseract-ocr-deu tesseract-ocr-ita tesseract-ocr-por")
        print("apt-get install -y tesseract-ocr-amh tesseract-ocr-afr tesseract-ocr-swa")

if __name__ == '__main__':
    setup_pythonanywhere()