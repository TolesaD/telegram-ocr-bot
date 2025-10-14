# test_ocr_fix.py
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

async def test_ocr():
    print("🧪 Testing OCR processor...")
    
    from utils.image_processing import ocr_processor
    
    # Test language mapping
    test_languages = ['english', 'spanish', 'french', 'german']
    for lang in test_languages:
        code = ocr_processor.get_language_code(lang)
        print(f"✅ {lang} -> {code}")
    
    # Test available engines
    print(f"🔧 Available engines: {list(ocr_processor.engines.keys())}")
    
    # Test Tesseract languages
    tesseract_langs = ocr_processor.get_tesseract_languages()
    print(f"🌐 Available Tesseract languages: {tesseract_langs}")
    
    print("🎉 OCR processor test completed successfully!")

if __name__ == '__main__':
    asyncio.run(test_ocr())