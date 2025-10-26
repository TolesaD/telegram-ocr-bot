# test_ocr.py
import logging
logging.basicConfig(level=logging.INFO)

try:
    from utils.unified_ocr import ultimate_ocr_processor
    print("✅ unified_ocr.py imports successfully")
    if ultimate_ocr_processor:
        print("✅ OCR processor created successfully")
    else:
        print("❌ OCR processor is None")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()