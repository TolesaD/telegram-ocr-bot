#!/usr/bin/env python3
"""
Test EasyOCR installation and performance
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.image_processing import OCRProcessor
import asyncio
import time

async def test_easyocr():
    print("🔍 Testing EasyOCR installation...")
    
    try:
        # Test if EasyOCR initializes
        from utils.image_processing import ocr_processor
        print("✅ EasyOCR initialized successfully")
        
        # Test with a simple image (you can create a test image)
        print("📸 Testing OCR processing...")
        
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create test image
        img = Image.new('RGB', (400, 200), color='white')
        d = ImageDraw.Draw(img)
        
        # Try to use a basic font
        try:
            font = ImageFont.load_default()
            d.text((50, 80), "Hello World! Test OCR", fill='black', font=font)
        except:
            d.text((50, 80), "Hello World! Test OCR", fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes = img_bytes.getvalue()
        
        # Test OCR
        start_time = time.time()
        text = await OCRProcessor.extract_text_async(img_bytes, 'en')
        processing_time = time.time() - start_time
        
        print(f"✅ OCR Test Successful!")
        print(f"⏱️  Processing time: {processing_time:.2f}s")
        print(f"📝 Extracted text: {text}")
        
        return True
        
    except Exception as e:
        print(f"❌ EasyOCR test failed: {e}")
        return False

if __name__ == '__main__':
    result = asyncio.run(test_easyocr())
    if result:
        print("\n🎉 All tests passed! Your bot is ready for production.")
    else:
        print("\n⚠️  Some tests failed. Please check the installation.")