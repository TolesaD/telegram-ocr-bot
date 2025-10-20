# test_languages.py
import pytesseract

print("🔍 Checking Tesseract setup...")
try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract version: {version}")
    
    langs = pytesseract.get_languages()
    print(f"🌍 Available languages: {langs}")
    
    # Test specific languages
    test_langs = ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor']
    for lang in test_langs:
        try:
            # Quick test
            from PIL import Image
            test_img = Image.new('RGB', (100, 30), color='white')
            pytesseract.image_to_string(test_img, lang=lang, config='--psm 8')
            print(f"✅ {lang} - AVAILABLE")
        except Exception as e:
            print(f"❌ {lang} - NOT AVAILABLE: {str(e)[:100]}")

except Exception as e:
    print(f"❌ Error: {e}")