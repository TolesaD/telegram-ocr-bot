# utils/smart_ocr.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple
import io
from PIL import Image, ImageEnhance, ImageFilter
import re

logger = logging.getLogger(__name__)

class SmartOCRProcessor:
    """BULLETPROOF OCR processor - Simple, reliable, works for ALL languages"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.available_languages = self._get_available_languages()
        self.setup_ocr_configs()
        logger.info(f"✅ BULLETPROOF OCR Processor ready with {len(self.available_languages)} languages")
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng', 'amh']
    
    def setup_ocr_configs(self):
        """Simple, reliable OCR configurations"""
        self.configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
        }
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """BULLETPROOF OCR extraction - Simple and reliable"""
        start_time = time.time()
        
        try:
            # Step 1: Simple preprocessing
            processed_img = await self._simple_preprocess(image_bytes)
            
            # Step 2: BULLETPROOF extraction strategy
            extracted_text = await self._bulletproof_extraction(processed_img)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_good_text(extracted_text):
                logger.info(f"✅ BULLETPROOF OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _simple_preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Simple, reliable preprocessing that works for all languages"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Simple contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            # Fallback to basic processing
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return np.array(image)
    
    async def _bulletproof_extraction(self, image: np.ndarray) -> str:
        """BULLETPROOF extraction that works for ALL languages"""
        loop = asyncio.get_event_loop()
        
        # STRATEGY 1: Try the most effective language combinations
        effective_combinations = [
            # Universal combination - covers most languages
            self._get_universal_language_group(),
            # English + Amharic specifically
            'eng+amh',
            # Individual languages as fallback
            'eng',
            'amh',
        ]
        
        for lang_group in effective_combinations:
            if not lang_group:
                continue
                
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang_group, self.configs['standard']
                )
                
                if text and self._is_good_text(text):
                    logger.info(f"✅ SUCCESS with: {lang_group} - {len(text.strip())} chars")
                    return text.strip()
                    
            except Exception as e:
                logger.debug(f"Attempt {lang_group} failed: {e}")
                continue
        
        # STRATEGY 2: If above fails, try individual major languages
        major_languages = ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor', 'rus', 'hin', 'spa', 'fra', 'deu']
        
        for lang in major_languages:
            if lang not in self.available_languages:
                continue
                
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, self.configs['standard']
                )
                
                if text and self._is_good_text(text):
                    logger.info(f"✅ SUCCESS with individual: {lang} - {len(text.strip())} chars")
                    return text.strip()
                    
            except Exception as e:
                logger.debug(f"Individual {lang} failed: {e}")
                continue
        
        return ""
    
    def _get_universal_language_group(self) -> str:
        """Create a universal language group that covers most languages"""
        # Priority languages that work well together
        priority_languages = [
            'eng',    # English (most common)
            'amh',    # Amharic
            'ara',    # Arabic
            'chi_sim', # Chinese
            'jpn',    # Japanese  
            'kor',    # Korean
            'rus',    # Russian
            'hin',    # Hindi
            'spa',    # Spanish
            'fra',    # French
            'deu',    # German
            'ita',    # Italian
            'por',    # Portuguese
        ]
        
        # Filter to available languages only
        available = [lang for lang in priority_languages if lang in self.available_languages]
        
        if not available:
            return 'eng'  # Fallback to English
        
        # Return combination of available languages (limit to 8 for performance)
        return '+'.join(available[:8])
    
    def _is_good_text(self, text: str) -> bool:
        """Simple, reliable text validation"""
        if not text:
            return False
        
        clean_text = text.strip()
        
        # Basic length check
        if len(clean_text) < 10:
            return False
        
        # Check for character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 4:
            return False
        
        # Check for reasonable structure
        lines = clean_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if len(non_empty_lines) < 1:
            return False
        
        # Check for excessive repetition (garbage detection)
        if len(clean_text) > 20:
            # Check if most characters are the same
            char_counts = {}
            for char in clean_text:
                if char.isalnum() or char.isspace():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                max_count = max(char_counts.values())
                if max_count / len(clean_text) > 0.5:  # 50% same character
                    return False
        
        return True

# Global instance
smart_ocr_processor = SmartOCRProcessor()