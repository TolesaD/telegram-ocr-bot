# utils/unified_ocr.py - FIXED VERSION
import logging
import asyncio
import time
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Any
import io
import re

logger = logging.getLogger(__name__)

# Try to import OpenCV with fallback
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    logger.info("✅ OpenCV imported successfully")
except ImportError as e:
    logger.error(f"❌ OpenCV import failed: {e}")
    OPENCV_AVAILABLE = False
    # Create dummy numpy for fallback
    class DummyNumpy:
        def __init__(self):
            self.uint8 = 'uint8'
            self.ones = lambda *args: None
        def frombuffer(self, *args, **kwargs):
            return None
        def array(self, *args, **kwargs):
            return None
    np = DummyNumpy()

# Try to import PIL with fallback
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
    logger.info("✅ PIL imported successfully")
except ImportError as e:
    logger.error(f"❌ PIL import failed: {e}")
    PILLOW_AVAILABLE = False

# Configure Tesseract path
try:
    import pytesseract
    TESSERACT_CMD = '/usr/bin/tesseract'
    if os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        logger.info(f"✅ Tesseract configured at: {TESSERACT_CMD}")
    else:
        logger.warning("❌ Tesseract not found at /usr/bin/tesseract")
        # Try to find tesseract in PATH
        import shutil
        tesseract_path = shutil.which('tesseract')
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"✅ Tesseract found in PATH: {tesseract_path}")
        else:
            logger.error("❌ Tesseract not found in system")
except ImportError as e:
    logger.error(f"❌ pytesseract import failed: {e}")
    pytesseract = None

class UltimateOCRProcessor:
    """ULTIMATE OCR Processor - Robust version with fallbacks"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)  # Reduced for Railway
        self.available_languages = self._get_available_languages()
        self.setup_ultimate_configs()
        logger.info(f"🚀 ULTIMATE OCR Processor ready with {len(self.available_languages)} languages")
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages with robust error handling"""
        try:
            if pytesseract is None:
                return ['eng']  # Fallback to English only
            
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng']  # Fallback to English only
    
    def setup_ultimate_configs(self):
        """Simple OCR configurations"""
        self.configs = {
            'universal': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7',
            'single_word': '--oem 3 --psm 8',
        }
    
    async def extract_text_ultimate(self, image_bytes: bytes) -> str:
        """ULTIMATE OCR extraction with robust error handling"""
        start_time = time.time()
        
        try:
            # Check if OCR is available
            if pytesseract is None:
                return "OCR service not available. Please check server configuration."
            
            # Step 1: Simple preprocessing
            processed_img = await self._simple_preprocess(image_bytes)
            
            if processed_img is None:
                return "Failed to process image."
            
            # Step 2: Simple extraction strategy
            extracted_text = await self._simple_extraction_strategy(processed_img)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_quality_text(extracted_text):
                logger.info(f"✅ OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _simple_preprocess(self, image_bytes: bytes):
        """Simple preprocessing that works without OpenCV"""
        try:
            if OPENCV_AVAILABLE:
                return await self._preprocess_with_opencv(image_bytes)
            elif PILLOW_AVAILABLE:
                return await self._preprocess_with_pil(image_bytes)
            else:
                logger.error("No image processing library available")
                return None
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return None
    
    async def _preprocess_with_opencv(self, image_bytes: bytes):
        """OpenCV preprocessing"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image with OpenCV")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Simple contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"OpenCV preprocessing failed: {e}")
            return await self._preprocess_with_pil(image_bytes)
    
    async def _preprocess_with_pil(self, image_bytes: bytes):
        """PIL preprocessing fallback"""
        try:
            if not PILLOW_AVAILABLE:
                return None
                
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return np.array(image)
            
        except Exception as e:
            logger.error(f"PIL preprocessing failed: {e}")
            return None
    
    async def _simple_extraction_strategy(self, image) -> str:
        """Simple extraction strategy with fallbacks"""
        if pytesseract is None:
            return ""
            
        loop = asyncio.get_event_loop()
        
        # Try different language combinations
        language_attempts = [
            'eng+amh',  # English + Amharic
            'eng',      # English only
            'amh',      # Amharic only
            '',         # Auto-detect
        ]
        
        for lang in language_attempts:
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, self.configs['universal']
                )
                
                if text and self._is_quality_text(text):
                    logger.info(f"✅ Success with language: {lang}")
                    return text.strip()
                    
            except Exception as e:
                logger.debug(f"Language {lang} failed: {e}")
                continue
        
        return ""
    
    def _is_quality_text(self, text: str) -> bool:
        """Simple text quality validation"""
        if not text:
            return False
        
        clean_text = text.strip()
        
        # Basic length check
        if len(clean_text) < 5:
            return False
        
        # Character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 3:
            return False
        
        # Check for excessive repetition
        if len(clean_text) > 10:
            char_counts = {}
            for char in clean_text:
                if char.isalnum():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                max_count = max(char_counts.values())
                if max_count / len(clean_text) > 0.7:
                    return False
        
        return True

# Global instance with error handling
try:
    ultimate_ocr_processor = UltimateOCRProcessor()
    logger.info("✅ Ultimate OCR Processor created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Ultimate OCR Processor: {e}")
    ultimate_ocr_processor = None