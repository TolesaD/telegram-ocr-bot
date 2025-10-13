import pytesseract
from PIL import Image, ImageEnhance
import io
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

class TesseractFallback:
    """Tesseract fallback for when EasyOCR fails"""
    
    @staticmethod
    def setup_tesseract_path():
        """Set Tesseract path"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                return True
        return False
    
    @staticmethod
    async def extract_text_async(image_bytes, language='eng'):
        """Async Tesseract text extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            TesseractFallback._extract_with_tesseract, 
            image_bytes, 
            language
        )
    
    @staticmethod
    def _extract_with_tesseract(image_bytes, language):
        """Extract text using Tesseract"""
        try:
            if not TesseractFallback.setup_tesseract_path():
                raise Exception("Tesseract not available")
            
            image = Image.open(io.BytesIO(image_bytes))
            
            # Simple preprocessing
            if image.mode != 'L':
                image = image.convert('L')
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Tesseract configuration
            custom_config = r'--oem 1 --psm 6 -c preserve_interword_spaces=1'
            
            text = pytesseract.image_to_string(
                image, 
                lang=language, 
                config=custom_config
            )
            
            return TesseractFallback._clean_extracted_text(text)
            
        except Exception as e:
            logger.error(f"Tesseract processing failed: {e}")
            raise
    
    @staticmethod
    def _clean_extracted_text(text):
        """Clean Tesseract output"""
        if not text:
            return "No readable text found."
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)