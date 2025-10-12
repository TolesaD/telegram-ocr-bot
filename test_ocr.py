import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.image_processing import ImageProcessor

def main():
    print("🧪 Testing Tesseract OCR Configuration")
    print("=" * 50)
    
    # Test 1: Check Tesseract availability
    print("1. Checking Tesseract...")
    if ImageProcessor.check_tesseract_availability():
        print("   ✅ Tesseract is working!")
    else:
        print("   ❌ Tesseract failed")
        return
    
    # Test 2: Check supported languages
    print("2. Checking languages...")
    languages = ImageProcessor.get_supported_languages()
    print(f"   ✅ Supported languages: {list(languages.keys())}")
    
    print("=" * 50)
    print("🎉 All tests passed! Your OCR is ready to use.")
    print("\n💡 You can now run your bot with: python bot.py")

if __name__ == "__main__":
    main()