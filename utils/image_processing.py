# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import (
    get_tesseract_code, get_amharic_config, is_amharic_character,
    detect_primary_language, clean_amharic_text, get_optimal_ocr_config
)

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Setup Tesseract with enhanced configuration"""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            return False
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with smart language detection"""
        start_time = time.time()
        
        try:
            # Enhanced preprocessing with script-specific adjustments
            processed_image, image_size = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.enhanced_preprocessing,
                image_bytes
            )
            
            # Smart language detection first
            detected_language = await self.detect_language_smart(processed_image)
            logger.info(f"🔍 Detected language: {detected_language}")
            
            # Extract text based on detected language with size-aware config
            if detected_language == 'am':
                text = await self.amharic_specific_ocr(processed_image, image_size)
            else:
                text = await self.english_or_auto_ocr(processed_image, detected_language, image_size)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                return "🔍 No readable text found. Please try a clearer image."
            
            # Enhanced text cleaning based on language
            cleaned_text = self.enhanced_clean_text(text, detected_language)
            
            logger.info(f"✅ {detected_language.upper()} OCR completed in {processing_time:.2f}s")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return f"❌ Processing error: {str(e)}"
    
    async def detect_language_smart(self, processed_image):
        """Enhanced language detection with better script support"""
        loop = asyncio.get_event_loop()
        
        try:
            # First try OSD for script detection
            osd_result = await loop.run_in_executor(
                thread_pool,
                self._get_osd_data,
                processed_image
            )
            
            # Extract script from OSD
            script = self._extract_script_from_osd(osd_result)
            logger.info(f"📜 OSD detected script: {script}")
            
            # Quick extraction with primary languages first
            test_texts = {}
            test_languages = ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor']
            
            for lang in test_languages:
                try:
                    text = await self.extract_with_tesseract(processed_image, lang, '--psm 6 --oem 1')
                    if text and len(text.strip()) > 3:
                        test_texts[lang] = text
                except:
                    continue
            
            # Analyze which language produced the best results
            best_lang = 'en'
            best_confidence = 0
            
            for lang, text in test_texts.items():
                # Convert Tesseract code to our language code
                lang_map = {'eng': 'en', 'amh': 'am', 'ara': 'ar', 'chi_sim': 'zh', 'jpn': 'ja', 'kor': 'ko'}
                current_lang = lang_map.get(lang, 'en')
                
                # Use language detection to validate
                detected_primary = detect_primary_language(text)
                
                if detected_primary == current_lang:
                    confidence = len(text.strip())
                    if confidence > best_confidence:
                        best_lang = current_lang
                        best_confidence = confidence
            
            # Fallback to script detection if no good match
            if best_confidence < 10:
                script_lang = self._get_language_from_script(script)
                if script_lang:
                    best_lang = script_lang
            
            logger.info(f"🎯 Final language selection: {best_lang}")
            return best_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def _get_osd_data(self, image):
        """Get OSD data from image"""
        try:
            return pytesseract.image_to_osd(image, config='--psm 0')
        except:
            return ""
    
    def _extract_script_from_osd(self, osd_result):
        """Extract script from OSD result"""
        if not osd_result:
            return "Unknown"
        
        for line in osd_result.split('\n'):
            if line.startswith('Script:'):
                return line.split(':')[1].strip()
        return "Unknown"
    
    def _get_language_from_script(self, script):
        """Convert script name to language code"""
        script_map = {
            "Amharic": "am",
            "Arabic": "ar", 
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko",
            "Latin": "en",
            "Cyrillic": "ru",
            "Devanagari": "hi"
        }
        return script_map.get(script, "en")
    
    def is_likely_english(self, text):
        """Check if text is likely English"""
        if not text:
            return False
        
        # Count English letters and common punctuation
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_chars = len(text)
        
        if total_chars < 5:
            return False
        
        # At least 60% should be English letters
        english_ratio = english_chars / total_chars
        return english_ratio > 0.6
    
    def is_likely_amharic(self, text):
        """Check if text is likely Amharic"""
        if not text:
            return False
        
        # Count Amharic characters
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        total_chars = len(text)
        
        if total_chars < 3:
            return False
        
        # At least 20% should be Amharic characters to be considered Amharic
        amharic_ratio = amharic_chars / total_chars
        return amharic_ratio > 0.2
    
    async def amharic_specific_ocr(self, processed_image, image_size):
        """Amharic-specific OCR processing with enhanced strategies"""
        strategies = [
            ('amh', get_optimal_ocr_config('am', image_size)),
            ('amh', '--oem 1 --psm 4'),  # Single column
            ('amh', '--oem 1 --psm 6'),  # Uniform block
            ('amh+eng', '--oem 1 --psm 6'),  # Fallback to English
        ]
        
        best_text = ""
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
                    # If we get good Amharic text, return early
                    if self.is_likely_amharic(text):
                        break
            except Exception as e:
                logger.warning(f"Amharic strategy {lang} failed: {e}")
                continue
        
        return best_text
    
    async def english_or_auto_ocr(self, processed_image, detected_language, image_size):
        """OCR for English and other non-Amharic languages"""
        strategies = [
            ('eng', get_optimal_ocr_config('en', image_size)),
            ('eng', '--oem 3 --psm 4'),   # Single column
            ('eng', '--oem 3 --psm 6'),   # Uniform block
            ('eng', '--oem 3 --psm 3'),   # Fully automatic
        ]
        
        # Add specific language strategies if detected
        if detected_language and detected_language != 'en' and detected_language != 'am':
            tesseract_lang = get_tesseract_code(detected_language)
            strategies.insert(0, (f'{tesseract_lang}+eng', get_optimal_ocr_config('en', image_size)))
        
        best_text = ""
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
                    # If we get good English text, return early
                    if self.is_likely_english(text):
                        break
            except Exception as e:
                logger.warning(f"English/Auto strategy {lang} failed: {e}")
                continue
        
        return best_text
    
    def enhanced_preprocessing(self, image_bytes):
        """Enhanced preprocessing that adapts to different scripts"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast - different levels for different scripts
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Increased contrast
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            # Resize if image is too small (improves OCR for small text)
            if min(image.size) < 500:
                scale_factor = 800 / min(image.size)
                new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image, original_size
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return image, image.size
    
    def enhanced_clean_text(self, text, language):
        """Enhanced text cleaning based on language"""
        if not text:
            return ""
        
        # Language-specific cleaning
        if language == 'am':
            text = clean_amharic_text(text)
        
        # General cleaning for all languages
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove lines that are mostly special characters or numbers
                if self.is_meaningful_line(line, language):
                    cleaned_line = self.fix_common_artifacts(line)
                    cleaned_lines.append(cleaned_line)
        
        # Remove duplicate lines while preserving order
        unique_lines = []
        for line in cleaned_lines:
            if line not in unique_lines:
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def is_meaningful_line(self, line, language):
        """Check if line contains meaningful content"""
        if len(line.strip()) < 2:
            return False
        
        # Count meaningful characters based on language
        if language == 'am':
            meaningful_chars = sum(1 for c in line if is_amharic_character(c) or c.isalpha())
        else:
            meaningful_chars = sum(1 for c in line if c.isalpha())
        
        total_chars = len(line)
        
        if total_chars == 0:
            return False
        
        # At least 30% should be meaningful characters
        return (meaningful_chars / total_chars) > 0.3
    
    def fix_common_artifacts(self, line):
        """Fix common OCR artifacts"""
        if not line:
            return line
        
        # Fix common character confusions
        replacements = {
            '|': 'I',
            '0': 'O',
            '1': 'I',
            '5': 'S',
            '8': 'B'
        }
        
        # Only replace if it makes sense in context
        words = line.split()
        cleaned_words = []
        
        for word in words:
            # Don't replace in likely numbers
            if not word.isdigit():
                for wrong, correct in replacements.items():
                    if wrong in word and len(word) > 1:
                        word = word.replace(wrong, correct)
            cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    async def extract_with_tesseract(self, image, lang, config):
        """Extract text with Tesseract"""
        loop = asyncio.get_event_loop()
        try:
            text = await loop.run_in_executor(
                thread_pool,
                self._tesseract_extract,
                image,
                lang,
                config
            )
            return text
        except Exception as e:
            logger.error(f"Tesseract extraction failed for {lang}: {e}")
            return ""
    
    def _tesseract_extract(self, image, lang, config):
        """Synchronous Tesseract extraction"""
        try:
            text = pytesseract.image_to_string(
                image,
                lang=lang,
                config=config,
                timeout=30
            )
            return text
        except Exception as e:
            logger.error(f"Tesseract error for {lang}: {e}")
            return ""

# Global instance
ocr_processor = OCRProcessor()

class PerformanceMonitor:
    def __init__(self):
        self.request_times = []
    
    def record_request(self, processing_time):
        self.request_times.append(processing_time)
        if len(self.request_times) > 100:
            self.request_times.pop(0)
    
    def get_stats(self):
        if not self.request_times:
            return "No requests yet"
        avg_time = sum(self.request_times) / len(self.request_times)
        return f"Average processing time: {avg_time:.2f}s"

performance_monitor = PerformanceMonitor()