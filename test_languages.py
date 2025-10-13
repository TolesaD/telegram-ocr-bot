#!/usr/bin/env python3
"""
Test multi-language OCR support
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.image_processing import ImageProcessor
import config

async def test_languages():
    print("🌐 Testing Multi-Language OCR Support...\n")
    
    # Create a simple test image with text
    from PIL import Image, ImageDraw
    import io
    
    # Test different languages
    test_languages = ['english', 'spanish', 'french', 'german']
    
    for lang in test_languages:
        if lang in config.SUPPORTED_LANGUAGES:
            lang_code = config.SUPPORTED_LANGUAGES[lang]
            display_name = config.LANGUAGE_DISPLAY_NAMES.get(lang, lang)
            
            print(f"Testing: {display_name} ({lang_code})")
            
            # Create test image
            img = Image.new('RGB', (400, 200), color='white')
            d = ImageDraw.Draw(img)
            
            # Add sample text
            if lang == 'english':
                text = "Hello World\nOCR Test"
            elif lang == 'spanish':
                text = "Hola Mundo\nPrueba OCR"
            elif lang == 'french':
                text = "Bonjour le Monde\nTest OCR"
            elif lang == 'german':
                text = "Hallo Welt\nOCR Test"
            else:
                text = "Test Text\nOCR"
            
            d.text((50, 80), text, fill='black')
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            
            try:
                result = await ImageProcessor.extract_text_async(img_bytes.getvalue(), lang_code)
                print(f"✅ {display_name}: SUCCESS")
                if "No readable text" not in result:
                    print(f"   Extracted: {result[:50]}...")
                else:
                    print(f"   No text detected")
            except Exception as e:
                print(f"❌ {display_name}: FAILED - {e}")
            
            print()
    
    print("🎉 Language testing completed!")

if __name__ == '__main__':
    asyncio.run(test_languages())