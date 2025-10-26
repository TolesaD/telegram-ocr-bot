# test_ocr.py
import asyncio
import requests
from utils.smart_ocr import smart_ocr_processor

async def test_ocr():
    """Test OCR with different language images"""
    
    # Test images (you can replace these with actual image URLs)
    test_images = {
        'English': 'https://example.com/english.jpg',
        'Amharic': 'https://example.com/amharic.jpg', 
        'Arabic': 'https://example.com/arabic.jpg',
        'Chinese': 'https://example.com/chinese.jpg',
    }
    
    for language, url in test_images.items():
        print(f"\n🧪 Testing {language}...")
        
        try:
            # Download image
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Process with OCR
            result = await smart_ocr_processor.extract_text_smart(response.content)
            
            print(f"✅ {language} Result: {result[:100]}...")
            
        except Exception as e:
            print(f"❌ {language} Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ocr())