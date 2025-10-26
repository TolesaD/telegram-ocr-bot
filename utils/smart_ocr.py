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
    """Smart OCR processor with balanced accuracy and reliability"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.setup_ocr_configs()
        
    def setup_ocr_configs(self):
        """Optimized OCR configurations for reliability"""
        self.configs = {
            # Standard configurations (more permissive)
            'english_standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'amharic_standard': '--oem 3 --psm 6 -c textord_min_linesize=1.8 -c preserve_interword_spaces=1',
            'auto': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7 -c preserve_interword_spaces=1'
        }
        
        logger.info("✅ Smart OCR Processor initialized")
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """Reliable OCR extraction with balanced accuracy"""
        start_time = time.time()
        
        try:
            # Step 1: Fast preprocessing
            processed_img = await asyncio.wait_for(
                self._fast_preprocess(image_bytes),
                timeout=5.0
            )
            
            # Step 2: Quick language detection
            probable_language = await asyncio.wait_for(
                self._quick_language_detection(processed_img),
                timeout=5.0
            )
            
            logger.info(f"🔍 Detected language: {probable_language}")
            
            # Step 3: Extract with reliable approach
            extracted_text = await asyncio.wait_for(
                self._reliable_extraction(processed_img, probable_language),
                timeout=15.0
            )
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_reasonable_text(extracted_text):
                logger.info(f"✅ OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                # Final fallback attempt
                final_text = await self._final_fallback(processed_img)
                if final_text and self._is_reasonable_text(final_text):
                    logger.info(f"✅ Fallback OCR completed in {processing_time:.2f}s")
                    return final_text
                else:
                    logger.warning("❌ No reasonable text extracted after all attempts")
                    return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _fast_preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Fast and reliable image preprocessing"""
        try:
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Simple resize if too large
            height, width = gray.shape
            if max(height, width) > 1200:
                scale = 1200 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # Basic contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Fast preprocessing failed: {e}")
            # Simple fallback
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return np.array(image)
    
    async def _quick_language_detection(self, image: np.ndarray) -> str:
        """Quick and reliable language detection"""
        loop = asyncio.get_event_loop()
        
        # Try quick English extraction
        try:
            english_text = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image, 'eng', self.configs['english_standard']
            )
            
            if english_text and self._looks_like_english(english_text):
                return 'english'
        except:
            pass
        
        # Try quick Amharic extraction
        try:
            amharic_text = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image, 'amh', self.configs['amharic_standard']
            )
            
            if amharic_text and self._looks_like_amharic(amharic_text):
                return 'amharic'
        except:
            pass
        
        # Default to auto
        return 'auto'
    
    async def _reliable_extraction(self, image: np.ndarray, language: str) -> str:
        """Reliable text extraction with fallbacks"""
        loop = asyncio.get_event_loop()
        
        strategies = {
            'english': [
                ('eng', self.configs['english_standard'], 'English Standard'),
                ('eng', self.configs['document'], 'English Document'),
            ],
            'amharic': [
                ('amh', self.configs['amharic_standard'], 'Amharic Standard'),
                ('amh', self.configs['document'], 'Amharic Document'),
            ],
            'auto': [
                ('eng', self.configs['auto'], 'Auto English'),
                ('amh', self.configs['auto'], 'Auto Amharic'),
                ('eng+amh', self.configs['auto'], 'Auto Combined'),
            ]
        }
        
        strategies_list = strategies.get(language, strategies['auto'])
        
        for lang, config, strategy_name in strategies_list:
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, config
                )
                
                if text and len(text.strip()) > 2:  # Lower threshold
                    logger.info(f"📊 {strategy_name}: {len(text.strip())} chars")
                    
                    # Basic validation
                    if self._is_reasonable_text(text):
                        return text.strip()
                        
            except Exception as e:
                logger.debug(f"Strategy {strategy_name} failed: {e}")
                continue
        
        return ""
    
    async def _final_fallback(self, image: np.ndarray) -> str:
        """Final fallback attempts"""
        loop = asyncio.get_event_loop()
        
        fallback_attempts = [
            ('eng', self.configs['single_line'], 'Fallback English'),
            ('amh', self.configs['single_line'], 'Fallback Amharic'),
            ('', self.configs['single_line'], 'Fallback Auto'),
        ]
        
        for lang, config, attempt_name in fallback_attempts:
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, config
                )
                
                if text and len(text.strip()) > 1:
                    logger.info(f"🔄 {attempt_name} found text: {len(text.strip())} chars")
                    return text.strip()
                    
            except Exception as e:
                logger.debug(f"Fallback {attempt_name} failed: {e}")
                continue
        
        return ""
    
    def _looks_like_english(self, text: str) -> bool:
        """Check if text looks like English (permissive)"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Count English characters
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_alpha = len([c for c in text if c.isalpha()])
        
        if total_alpha == 0:
            return False
        
        # Lower threshold for English detection
        return (english_chars / total_alpha) > 0.6
    
    def _looks_like_amharic(self, text: str) -> bool:
        """Check if text looks like Amharic (permissive)"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Count Amharic characters
        amharic_chars = sum(1 for c in text if '\u1200' <= c <= '\u137F')
        total_alpha = len([c for c in text if c.isalpha()])
        
        if total_alpha == 0:
            return False
        
        # Lower threshold for Amharic detection
        return (amharic_chars / total_alpha) > 0.2
    
    def _is_reasonable_text(self, text: str) -> bool:
        """Check if text is reasonable (permissive validation)"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Remove whitespace and check minimum length
        clean_text = text.strip()
        if len(clean_text) < 3:
            return False
        
        # Check for reasonable character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 2:
            return False
        
        # Check if it's not just repeated characters
        if len(clean_text) > 5:
            repeated_ratio = max(clean_text.count(c) for c in clean_text) / len(clean_text)
            if repeated_ratio > 0.8:  # 80% same character
                return False
        
        # Basic garbage detection
        if self._is_obvious_garbage(text):
            return False
        
        return True
    
    def _is_obvious_garbage(self, text: str) -> bool:
        """Detect obvious garbage text"""
        if not text:
            return True
        
        # Too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars / len(text) > 0.5:
            return True
        
        # Repeated nonsense patterns
        nonsense_patterns = [
            r'^[^a-zA-Z\u1200-\u137F]*$',  # No letters at all
            r'(.)\1{5,}',  # Same character repeated 6+ times
        ]
        
        for pattern in nonsense_patterns:
            if re.search(pattern, text):
                return True
        
        return False

# Global instance
smart_ocr_processor = SmartOCRProcessor()