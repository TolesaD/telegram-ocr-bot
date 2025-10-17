# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import get_tesseract_code, get_amharic_config, is_amharic_character

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
            # Gentle preprocessing
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.preservative_preprocessing,
                image_bytes
            )
            
            # Smart language detection first
            detected_language = await self.detect_language_smart(processed_image)
            logger.info(f"🔍 Detected language: {detected_language}")
            
            # Extract text based on detected language
            if detected_language == 'amh':
                text = await self.amharic_specific_ocr(processed_image, image_bytes)
            else:
                text = await self.english_or_auto_ocr(processed_image, detected_language)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                return "🔍 No readable text found. Please try a clearer image."
            
            # Clean text while preserving formatting
            cleaned_text = self.preservative_clean_text(text)
            
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
            
            # Try quick extraction with multiple languages to verify
            test_texts = {}
            test_languages = ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor']
            
            for lang in test_languages:
                try:
                    text = await self.extract_with_tesseract(processed_image, lang, '--psm 6 --oem 1')
                    if text:
                        test_texts[lang] = text
                except:
                    continue
            
            # Analyze which language produced the best results
            best_lang = 'eng'
            best_confidence = 0
            
            for lang, text in test_texts.items():
                script = self._detect_script_from_text(text)
                expected_lang = self._get_language_from_script(script)
                
                # Convert Tesseract code to our language code
                lang_map = {'eng': 'en', 'amh': 'am', 'ara': 'ar', 'chi_sim': 'zh', 'jpn': 'ja', 'kor': 'ko'}
                current_lang = lang_map.get(lang, 'en')
                
                is_valid, message = self._validate_text_quality(text, current_lang)
                if is_valid and len(text) > best_confidence:
                    best_lang = current_lang
                    best_confidence = len(text)
            
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
    
    def _detect_script_from_text(self, text):
        """Detect script from text content"""
        if not text:
            return "Unknown"
        
        # Simple script detection based on character ranges
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        japanese_chars = sum(1 for c in text if ('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF'))
        korean_chars = sum(1 for c in text if '\uAC00' <= c <= '\uD7A3')
        
        if amharic_chars > 0:
            return "Amharic"
        elif arabic_chars > 0:
            return "Arabic"
        elif chinese_chars > 0:
            return "Chinese"
        elif japanese_chars > 0:
            return "Japanese"
        elif korean_chars > 0:
            return "Korean"
        elif english_chars > 0:
            return "Latin"
        else:
            return "Unknown"
    
    def _get_language_from_script(self, script):
        """Convert script name to language code"""
        script_map = {
            "Amharic": "am",
            "Arabic": "ar", 
            "Chinese": "zh",
            "Japanese": "ja",
            "Korean": "ko",
            "Latin": "en"
        }
        return script_map.get(script, "en")
    
    def _validate_text_quality(self, text, language):
        """Validate text quality for a given language"""
        if not text or len(text.strip()) < 3:
            return False, "Text too short"
        
        # Basic validation - check if text has reasonable character diversity
        unique_chars = len(set(text))
        if unique_chars < 2:
            return False, "Not enough character diversity"
        
        return True, "Valid text"
    
    def is_likely_english(self, text):
        """Check if text is likely English"""
        if not text:
            return False
        
        # Count English letters and common punctuation
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        total_chars = len(text)
        
        if total_chars < 5:
            return False
        
        # At least 70% should be English letters
        english_ratio = english_chars / total_chars
        return english_ratio > 0.7
    
    def is_likely_amharic(self, text):
        """Check if text is likely Amharic"""
        if not text:
            return False
        
        # Count Amharic characters
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        total_chars = len(text)
        
        if total_chars < 3:
            return False
        
        # At least 30% should be Amharic characters to be considered Amharic
        amharic_ratio = amharic_chars / total_chars
        return amharic_ratio > 0.3
    
    async def amharic_specific_ocr(self, processed_image, original_image_bytes):
        """Amharic-specific OCR processing"""
        strategies = [
            ('amh+amh_vert', get_amharic_config()),
            ('amh+amh_vert', '--oem 1 --psm 6'),
            ('amh', '--oem 1 --psm 4'),
            ('amh+eng', '--oem 1 --psm 6'),  # Fallback to English if needed
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
    
    async def english_or_auto_ocr(self, processed_image, detected_language):
        """OCR for English and other non-Amharic languages"""
        strategies = [
            ('eng', '--oem 3 --psm 6'),   # English, uniform block
            ('eng', '--oem 3 --psm 3'),   # English, fully automatic
            ('osd', '--oem 3 --psm 3'),   # Auto script detection
            ('eng+osd', '--oem 3 --psm 6'), # English with auto-detection fallback
        ]
        
        # Add specific language strategies if detected
        if detected_language and detected_language != 'eng' and detected_language != 'amh':
            strategies.insert(0, (f'{detected_language}+eng', '--oem 3 --psm 6'))
        
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
    
    def preservative_preprocessing(self, image_bytes):
        """Gentle preprocessing that preserves original character shapes"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            # Very gentle contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            
            # Mild sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def preservative_clean_text(self, text):
        """Clean text while preserving original formatting and bullets"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            original_line = line.rstrip()
            
            if original_line:
                # Fix common OCR artifacts while preserving meaningful characters
                cleaned_line = self.fix_ocr_artifacts(original_line)
                cleaned_lines.append(cleaned_line)
            else:
                # Preserve empty lines for paragraph separation
                cleaned_lines.append('')
        
        # Join back with original line breaks
        result = '\n'.join(cleaned_lines)
        return result.strip()
    
    def fix_ocr_artifacts(self, line):
        """Fix common OCR artifacts while preserving original characters"""
        if not line:
            return line
        
        # Fix bullet artifacts
        bullet_replacements = {
            'e ': '• ',
            'o ': '• ',
            '0 ': '• ',
            'c ': '• ',
            'E ': '• ',
            'O ': '• ',
            'C ': '• ',
            'point ': '• ',
            '° ': '• ',
            '· ': '• ',
        }
        
        # Check if line starts with a bullet pattern
        for wrong_bullet, correct_bullet in bullet_replacements.items():
            if line.startswith(wrong_bullet):
                line = line.replace(wrong_bullet, correct_bullet, 1)
                break
        
        return line
    
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