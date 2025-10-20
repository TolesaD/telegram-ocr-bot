# railway_check.py
import os
import sys
import subprocess

def check_tesseract_installation():
    print("🔍 Checking Tesseract installation on Railway...")
    
    # Check if Tesseract is installed
    try:
        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Tesseract found at: {result.stdout.strip()}")
        else:
            print("❌ Tesseract not found in PATH")
    except Exception as e:
        print(f"❌ Error checking Tesseract: {e}")
    
    # Check Tesseract version
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Tesseract version:\n{result.stdout}")
        else:
            print(f"❌ Tesseract version check failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error getting Tesseract version: {e}")
    
    # Check TESSDATA_PREFIX
    tessdata_prefix = os.getenv('TESSDATA_PREFIX', 'Not set')
    print(f"📁 TESSDATA_PREFIX: {tessdata_prefix}")
    
    # Check if tessdata directory exists
    if tessdata_prefix and tessdata_prefix != 'Not set':
        if os.path.exists(tessdata_prefix):
            print(f"✅ TESSDATA_PREFIX directory exists")
            files = os.listdir(tessdata_prefix)
            trained_files = [f for f in files if f.endswith('.traineddata')]
            print(f"📄 Found {len(trained_files)} language files")
            if trained_files:
                print(f"   Sample languages: {trained_files[:10]}...")
        else:
            print(f"❌ TESSDATA_PREFIX directory does not exist: {tessdata_prefix}")

if __name__ == "__main__":
    check_tesseract_installation()