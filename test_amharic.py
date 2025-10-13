# test_amharic.py
import pytesseract
from PIL import Image
import os

def test_amharic():
    print("🔍 Testing Amharic language support...")
    
    # Set Tesseract path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Check if Amharic file exists
    tessdata_path = r'C:\Program Files\Tesseract-OCR\tessdata\amh.traineddata'
    if os.path.exists(tessdata_path):
        print("✅ Amharic language file found!")
    else:
        print("❌ Amharic language file NOT found!")
        return
    
    # Test if Tesseract can load Amharic
    try:
        # Create a simple test image with Amharic text
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image
        img = Image.new('RGB', (400, 200), color='white')
        d = ImageDraw.Draw(img)
        
        # Try to draw some Amharic text (you can replace this with actual Amharic characters)
        try:
            # This might not display correctly without Amharic font, but we're testing OCR
            d.text((50, 80), "Amharic Test", fill='black')
        except:
            d.text((50, 80), "OCR Test", fill='black')
        
        # Test OCR with Amharic
        text = pytesseract.image_to_string(img, lang='amh')
        print("✅ Amharic OCR test successful!")
        print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        
    except Exception as e:
        print(f"❌ Amharic test failed: {e}")

if __name__ == '__main__':
    test_amharic()