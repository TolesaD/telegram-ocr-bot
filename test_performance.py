#!/usr/bin/env python3
"""
Test OCR performance with current setup
"""
import asyncio
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.image_processing import ImageProcessor

async def test_performance():
    print("🧪 Testing OCR Performance...")
    
    # Create a simple test image
    from PIL import Image, ImageDraw
    import io
    
    # Create test image with text
    img = Image.new('RGB', (800, 400), color='white')
    d = ImageDraw.Draw(img)
    
    # Add text
    text_lines = [
        "This is a test image for OCR",
        "Performance testing",
        "Multiple lines of text",
        "To check processing speed"
    ]
    
    y_position = 50
    for line in text_lines:
        d.text((50, y_position), line, fill='black')
        y_position += 40
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_data = img_bytes.getvalue()
    
    print(f"📐 Image size: {len(img_data)} bytes")
    
    # Test OCR performance
    start_time = time.time()
    
    try:
        text = await ImageProcessor.extract_text_async(img_data, 'eng')
        processing_time = time.time() - start_time
        
        print(f"✅ OCR completed in {processing_time:.2f} seconds")
        print(f"📝 Extracted text:\n{text}")
        
        if processing_time > 10:
            print("⚠️  Processing time is high - consider image optimization")
        else:
            print("🎉 Performance is good!")
            
    except Exception as e:
        print(f"❌ OCR failed: {e}")

if __name__ == '__main__':
    asyncio.run(test_performance())