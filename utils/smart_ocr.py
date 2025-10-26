# utils/smart_ocr.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import io
from PIL import Image
import re

logger = logging.getLogger(__name__)

class HybridOCRProcessor:
    """Hybrid OCR processor with strict language validation"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.available_languages = self._detect_available_languages()
        self.setup_environment_specific_configs()
        
    def _detect_available_languages(self) -> list:
        """Detect which languages are available"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {langs}")
            
            if len(langs) <= 5:
                logger.info("🔧 Limited language environment detected (Local)")
                self.environment = "local"
            else:
                logger.info("🚀 Full language environment detected (Railway)")
                self.environment = "railway"
                
            return langs
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng']
    
    def setup_environment_specific_configs(self):
        """Setup configurations based on environment"""
        self.universal_configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7 -c preserve_interword_spaces=1',
            'blurry': '--oem 3 --psm 6 -c textord_min_linesize=0.8',
        }
        
        logger.info(f"✅ Hybrid OCR initialized for {self.environment} environment")
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """Smart OCR extraction with accurate language detection"""
        start_time = time.time()
        
        try:
            # Preprocessing
            processed_img, quality_info = await asyncio.wait_for(
                self._enhanced_preprocess(image_bytes),
                timeout=4.0
            )
            
            logger.info(f"🔍 Image quality: {quality_info['quality']} (blur: {quality_info['blur_score']:.1f})")
            
            # Smart extraction based on environment
            if self.environment == "railway":
                extracted_text = await self._railway_extraction(processed_img, quality_info)
            else:
                extracted_text = await self._local_extraction(processed_img, quality_info)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_valid_text(extracted_text):
                detected_lang = self._detect_primary_language(extracted_text)
                logger.info(f"✅ {detected_lang} extraction completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _railway_extraction(self, image: np.ndarray, quality_info: dict) -> str:
        """Railway extraction with 70+ languages"""
        loop = asyncio.get_event_loop()
        
        config = self.universal_configs['standard']
        
        # Try major language combinations
        language_attempts = [
            'eng',  # English first
            'amh',  # Amharic second
            'eng+amh+ara+fra+spa+deu',  # Major languages
            'amh+eng',  # Alternative order
        ]
        
        best_text = ""
        best_lang = ""
        
        for lang in language_attempts:
            try:
                # Filter available languages
                available_lang = '+'.join([l for l in lang.split('+') if l in self.available_languages])
                if not available_lang:
                    continue
                
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, available_lang, config
                )
                
                if text and len(text.strip()) > 10:
                    detected_lang = self._detect_primary_language(text)
                    logger.info(f"🌐 [{available_lang}]: {len(text.strip())} chars -> {detected_lang}")
                    
                    # Only accept if the detected language matches what we tried to extract
                    if self._is_correct_language(text, lang):
                        if len(text.strip()) > len(best_text):
                            best_text = text.strip()
                            best_lang = detected_lang
                        
                        # Early exit for good matches
                        if detected_lang in lang.split('+') and len(text.strip()) > 50:
                            break
                            
            except Exception as e:
                logger.debug(f"Railway attempt {lang} failed: {e}")
                continue
        
        return best_text
    
    async def _local_extraction(self, image: np.ndarray, quality_info: dict) -> str:
        """Local extraction with strict language validation"""
        loop = asyncio.get_event_loop()
        
        config = self.universal_configs['standard']
        
        # Try both languages with strict validation
        extraction_attempts = [
            # English first with strict validation
            ('eng', 'English', self._is_definitely_english),
            # Amharic with strict validation
            ('amh', 'Amharic', self._is_definitely_amharic),
            # Combined with careful validation
            ('eng+amh', 'English+Amharic', self._is_reasonable_mixed_text),
            ('amh+eng', 'Amharic+English', self._is_reasonable_mixed_text),
        ]
        
        for lang, lang_name, validator in extraction_attempts:
            try:
                # Skip if language not available
                if not all(l in self.available_languages for l in lang.split('+')):
                    continue
                
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, config
                )
                
                if text and len(text.strip()) > 5:
                    actual_lang = self._detect_primary_language(text)
                    logger.info(f"🔧 {lang_name}: {len(text.strip())} chars -> Actually: {actual_lang}")
                    
                    # STRICT validation: text must match what we tried to extract
                    if validator(text) and actual_lang in lang_name:
                        logger.info(f"✅ {lang_name} validation PASSED")
                        return text.strip()
                    else:
                        logger.info(f"❌ {lang_name} validation FAILED - actually {actual_lang}")
                        
            except Exception as e:
                logger.debug(f"Local attempt {lang_name} failed: {e}")
                continue
        
        return ""
    
    def _is_definitely_english(self, text: str) -> bool:
        """STRICT English validation"""
        if not text or len(text.strip()) < 10:
            return False
        
        clean_text = text.strip()
        
        # Count proper English characters
        english_chars = sum(1 for c in clean_text if c.isalpha() and c.isascii())
        total_alpha = len([c for c in clean_text if c.isalpha()])
        
        if total_alpha == 0:
            return False
        
        # Must be predominantly English (>80%)
        english_ratio = english_chars / total_alpha
        if english_ratio < 0.8:
            return False
        
        # Check for common English words
        common_english_words = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'your', 'have', 'with', 'this', 'that', 'from']
        words = clean_text.lower().split()
        english_word_count = sum(1 for word in words if word in common_english_words)
        
        # Should have at least some common English words
        if english_word_count < 2:
            return False
        
        # Check for reasonable word lengths (English typically 2-10 chars)
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 2 or avg_word_length > 12:
            return False
        
        return True
    
    def _is_definitely_amharic(self, text: str) -> bool:
        """STRICT Amharic validation"""
        if not text or len(text.strip()) < 8:
            return False
        
        clean_text = text.strip()
        
        # Count actual Amharic characters (Ethiopic range)
        amharic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137F')
        total_chars = len(clean_text)
        
        if total_chars == 0:
            return False
        
        # Must be predominantly Amharic (>40% Amharic characters)
        amharic_ratio = amharic_chars / total_chars
        if amharic_ratio < 0.4:
            return False
        
        # Should have a reasonable number of Amharic characters
        if amharic_chars < 5:
            return False
        
        # Check for Amharic-specific patterns (multiple consecutive Amharic chars)
        amharic_sequences = re.findall(r'[\u1200-\u137F]{2,}', clean_text)
        if len(amharic_sequences) < 2:
            return False
        
        return True
    
    def _is_reasonable_mixed_text(self, text: str) -> bool:
        """Validation for mixed language text"""
        if not text or len(text.strip()) < 15:
            return False
        
        clean_text = text.strip()
        
        # Check for both English and Amharic content
        english_chars = sum(1 for c in clean_text if c.isalpha() and c.isascii())
        amharic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137F')
        total_alpha = len([c for c in clean_text if c.isalpha()])
        
        if total_alpha == 0:
            return False
        
        # Should have both English and Amharic characters
        if english_chars == 0 or amharic_chars == 0:
            return False
        
        # Both should be present in reasonable amounts
        english_ratio = english_chars / total_alpha
        amharic_ratio = amharic_chars / total_alpha
        
        return english_ratio > 0.2 and amharic_ratio > 0.2
    
    def _is_correct_language(self, text: str, attempted_lang: str) -> bool:
        """Check if extracted text matches attempted language"""
        actual_lang = self._detect_primary_language(text)
        
        if 'eng' in attempted_lang and actual_lang == "English":
            return True
        elif 'amh' in attempted_lang and actual_lang == "Amharic":
            return True
        elif 'amh' in attempted_lang and 'eng' in attempted_lang and actual_lang == "Mixed":
            return True
        else:
            return False
    
    def _detect_primary_language(self, text: str) -> str:
        """Accurately detect the primary language of text"""
        if not text:
            return "Unknown"
        
        clean_text = text.strip()
        
        # Count characters by script
        english_chars = sum(1 for c in clean_text if c.isalpha() and c.isascii())
        amharic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137F')
        total_alpha = len([c for c in clean_text if c.isalpha()])
        
        if total_alpha == 0:
            return "Unknown"
        
        english_ratio = english_chars / total_alpha
        amharic_ratio = amharic_chars / total_alpha
        
        # Strict thresholds
        if amharic_ratio > 0.6:
            return "Amharic"
        elif english_ratio > 0.8:
            return "English"
        elif amharic_ratio > 0.3 and english_ratio > 0.3:
            return "Mixed"
        elif amharic_ratio > 0.2:
            return "Mostly Amharic"
        elif english_ratio > 0.2:
            return "Mostly English"
        else:
            return "Other"
    
    def _is_valid_text(self, text: str) -> bool:
        """Basic text validation"""
        return text and len(text.strip()) > 5 and len(set(text.strip())) > 3
    
    async def _enhanced_preprocess(self, image_bytes: bytes) -> tuple:
        """Enhanced preprocessing"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Quality analysis
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            contrast = gray.std()
            
            quality_info = {
                'blur_score': blur_score,
                'contrast': contrast,
                'quality': 'excellent' if blur_score > 1000 else 'good' if blur_score > 100 else 'poor'
            }
            
            # Simple enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            return enhanced, quality_info
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            img_array = np.array(image)
            quality_info = {'blur_score': 100, 'contrast': 50, 'quality': 'unknown'}
            return img_array, quality_info

# Global instance
smart_ocr_processor = HybridOCRProcessor()