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
        self.available_languages = []
        self._load_available_languages()
    
    def setup_tesseract(self):
        """Setup Tesseract with Railway-specific configuration"""
        try:
            # Check if we're on Railway
            is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
            
            if is_railway:
                # On Railway, Tesseract should be in standard Linux path
                pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
                logger.info("🚄 Railway environment detected - using system Tesseract")
            else:
                # On local Windows, use default detection
                logger.info("💻 Local environment detected - using default Tesseract")
                
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized successfully")
            
            # Verify Tesseract is working
            test_image = Image.new('RGB', (100, 30), color='white')
            test_text = pytesseract.image_to_string(test_image, config='--psm 8')
            logger.info("✅ Tesseract test completed successfully")
            
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            
            # Try to find Tesseract on Railway
            if os.getenv('RAILWAY_ENVIRONMENT'):
                logger.info("🔍 Searching for Tesseract on Railway...")
                possible_paths = [
                    '/usr/bin/tesseract',
                    '/usr/local/bin/tesseract',
                    '/bin/tesseract'
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"✅ Found Tesseract at: {path}")
                        try:
                            version = pytesseract.get_tesseract_version()
                            logger.info(f"✅ Tesseract v{version} now working")
                            return True
                        except:
                            continue
            
            logger.error("❌ Could not find working Tesseract installation")
            return False
    
    def _load_available_languages(self):
        """Load available Tesseract languages"""
        try:
            # Method 1: Use pytesseract's built-in method
            try:
                self.available_languages = pytesseract.get_languages()
                logger.info(f"📚 Found {len(self.available_languages)} available languages: {self.available_languages}")
            except Exception as e:
                logger.warning(f"Could not get languages via pytesseract: {e}")
                # Method 2: Test common languages
                self._test_common_languages()
            
        except Exception as e:
            logger.error(f"Error loading available languages: {e}")
            self.available_languages = ['eng']  # Always fallback to English
    
    def _test_common_languages(self):
        """Test common languages to see what's available"""
        common_langs = ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor', 'spa', 'fra', 'deu', 'rus']
        available = []
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 30), color='white')
        
        for lang in common_langs:
            try:
                # Quick test to see if language is available
                pytesseract.image_to_string(test_image, lang=lang, config='--psm 8 -c min_characters_to_try=1')
                available.append(lang)
                logger.info(f"✅ Language {lang} is available")
            except Exception as e:
                logger.info(f"❌ Language {lang} is not available: {str(e)[:100]}")
                continue
        
        self.available_languages = available if available else ['eng']
        logger.info(f"🎯 Using available languages: {self.available_languages}")
    
    def is_language_available(self, lang_code):
        """Check if a language is available"""
        tesseract_code = self._get_tesseract_code_from_lang(lang_code)
        return tesseract_code in self.available_languages
    
    def _get_tesseract_code_from_lang(self, lang_code):
        """Convert our language code to Tesseract code"""
        mapping = {
            'en': 'eng', 'eng': 'eng', 'english': 'eng',
            'am': 'amh', 'amh': 'amh', 'amharic': 'amh',
            'ar': 'ara', 'ara': 'ara', 'arabic': 'ara',
            'zh': 'chi_sim', 'chi_sim': 'chi_sim', 'chinese': 'chi_sim',
            'ja': 'jpn', 'jpn': 'jpn', 'japanese': 'jpn',
            'ko': 'kor', 'kor': 'kor', 'korean': 'kor',
            'es': 'spa', 'spa': 'spa', 'spanish': 'spa',
            'fr': 'fra', 'fra': 'fra', 'french': 'fra',
            'de': 'deu', 'deu': 'deu', 'german': 'deu',
            'ru': 'rus', 'rus': 'rus', 'russian': 'rus'
        }
        return mapping.get(lang_code, 'eng')  # Default to English
    
    def _get_lang_from_tesseract_code(self, tess_code):
        """Convert Tesseract code to our language code"""
        mapping = {
            'eng': 'en', 'amh': 'am', 'ara': 'ar', 'chi_sim': 'zh',
            'jpn': 'ja', 'kor': 'ko', 'spa': 'es', 'fra': 'fr',
            'deu': 'de', 'rus': 'ru', 'por': 'pt', 'ita': 'it'
        }
        return mapping.get(tess_code, 'en')
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with Railway fallback"""
        start_time = time.time()
        
        try:
            # First, verify Tesseract is working
            if not await self.verify_tesseract_working():
                logger.error("❌ Tesseract not working, using fallback message")
                return "🔧 OCR service is temporarily unavailable. Please try again later or contact support."
            
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
            if detected_language == 'am':
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
            return "❌ OCR processing failed. Please try again with a different image."
    
    async def verify_tesseract_working(self):
        """Verify Tesseract is working on Railway"""
        try:
            test_image = Image.new('RGB', (100, 30), color='white')
            test_text = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                pytesseract.image_to_string,
                test_image,
                '--psm 8'
            )
            return True
        except Exception as e:
            logger.error(f"❌ Tesseract verification failed: {e}")
            return False
    
    async def detect_language_smart(self, processed_image):
        """Enhanced language detection that only uses available languages"""
        loop = asyncio.get_event_loop()
        
        try:
            logger.info(f"📚 Available languages for detection: {self.available_languages}")
            
            # Priority languages that are actually available
            priority_langs = []
            for lang in ['en', 'am', 'ar', 'zh', 'ja', 'ko']:
                if self.is_language_available(lang):
                    priority_langs.append(lang)
            
            # If no priority languages available, use whatever is available
            if not priority_langs:
                for tess_code in self.available_languages:
                    lang_code = self._get_lang_from_tesseract_code(tess_code)
                    if lang_code and lang_code not in priority_langs:
                        priority_langs.append(lang_code)
            
            logger.info(f"🎯 Testing languages: {priority_langs}")
            
            # Try quick extraction with available languages
            test_texts = {}
            for lang in priority_langs:
                try:
                    tesseract_code = self._get_tesseract_code_from_lang(lang)
                    text = await self.extract_with_tesseract(processed_image, tesseract_code, '--psm 6 --oem 1')
                    if text and text.strip():
                        test_texts[lang] = text
                        logger.info(f"✅ {lang} test successful: {len(text)} chars")
                except Exception as e:
                    logger.warning(f"❌ {lang} test failed: {e}")
                    continue
            
            # Analyze which language produced the best results
            best_lang = 'en'  # Default to English
            best_confidence = 0
            
            for lang, text in test_texts.items():
                confidence = self._calculate_text_confidence(text, lang)
                logger.info(f"📊 {lang} confidence: {confidence:.2f}")
                if confidence > best_confidence:
                    best_lang = lang
                    best_confidence = confidence
            
            # If no good results, try OSD as fallback
            if best_confidence < 0.3:
                osd_lang = await self._try_osd_detection(processed_image)
                if osd_lang and self.is_language_available(osd_lang):
                    best_lang = osd_lang
                    logger.info(f"🔄 Using OSD detected language: {best_lang}")
            
            logger.info(f"🎯 Final language selection: {best_lang} (confidence: {best_confidence:.2f})")
            return best_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def _calculate_text_confidence(self, text, language):
        """Calculate confidence score for detected text"""
        if not text or len(text.strip()) < 3:
            return 0
        
        text = text.strip()
        total_chars = len(text)
        
        if language == 'am':
            # Count Amharic characters
            amharic_chars = sum(1 for c in text if ('\u1200' <= c <= '\u137F'))
            return amharic_chars / total_chars if total_chars > 0 else 0
        
        elif language in ['ar', 'ara']:
            # Count Arabic characters
            arabic_chars = sum(1 for c in text if ('\u0600' <= c <= '\u06FF'))
            return arabic_chars / total_chars if total_chars > 0 else 0
        
        elif language in ['zh', 'chi_sim']:
            # Count Chinese characters
            chinese_chars = sum(1 for c in text if ('\u4e00' <= c <= '\u9fff'))
            return chinese_chars / total_chars if total_chars > 0 else 0
        
        elif language in ['ja', 'jpn']:
            # Count Japanese characters (Hiragana, Katakana, Kanji)
            japanese_chars = sum(1 for c in text if (
                '\u3040' <= c <= '\u309F' or  # Hiragana
                '\u30A0' <= c <= '\u30FF' or  # Katakana  
                '\u4e00' <= c <= '\u9fff'     # Kanji
            ))
            return japanese_chars / total_chars if total_chars > 0 else 0
        
        elif language in ['ko', 'kor']:
            # Count Korean characters
            korean_chars = sum(1 for c in text if ('\uAC00' <= c <= '\uD7A3'))
            return korean_chars / total_chars if total_chars > 0 else 0
        
        else:  # Default to English/Latin
            # Count English letters and common punctuation
            english_chars = sum(1 for c in text if (c.isalpha() and c.isascii()))
            return english_chars / total_chars if total_chars > 0 else 0
    
    async def _try_osd_detection(self, image):
        """Try OSD (Orientation and Script Detection)"""
        try:
            osd_data = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self._get_osd_data,
                image
            )
            
            if osd_data:
                for line in osd_data.split('\n'):
                    if line.startswith('Script:'):
                        script = line.split(':')[1].strip()
                        script_to_lang = {
                            'Latin': 'en',
                            'Cyrillic': 'ru', 
                            'Arabic': 'ar',
                            'Devanagari': 'hi',
                            'HanS': 'zh',
                            'Hangul': 'ko',
                            'Japanese': 'ja',
                            'Amharic': 'am',
                            'Ethiopic': 'am'
                        }
                        detected_lang = script_to_lang.get(script, 'en')
                        logger.info(f"📜 OSD detected script: {script} -> language: {detected_lang}")
                        return detected_lang
        except Exception as e:
            logger.warning(f"OSD detection failed: {e}")
        return None
    
    def _get_osd_data(self, image):
        """Get OSD data from image"""
        try:
            return pytesseract.image_to_osd(image, config='--psm 0')
        except:
            return ""
    
    async def amharic_specific_ocr(self, processed_image, original_image_bytes):
        """Amharic-specific OCR processing - only if Amharic is available"""
        strategies = []
        
        if self.is_language_available('am'):
            strategies.extend([
                ('amh', get_amharic_config()),
                ('amh', '--oem 1 --psm 6'),
                ('amh', '--oem 1 --psm 4'),
            ])
        
        # Always include English as fallback
        if self.is_language_available('en'):
            strategies.append(('eng', '--oem 1 --psm 6'))
        
        best_text = ""
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
                    # If we get good Amharic text, return early
                    if lang == 'amh' and self.is_likely_amharic(text):
                        logger.info(f"✅ Good Amharic text found with {lang}")
                        break
            except Exception as e:
                logger.warning(f"Amharic strategy {lang} failed: {e}")
                continue
        
        return best_text
    
    async def english_or_auto_ocr(self, processed_image, detected_language):
        """OCR for English and other non-Amharic languages - only available ones"""
        strategies = []
        
        # Add specific language if detected and available
        if detected_language and detected_language != 'en' and detected_language != 'am':
            if self.is_language_available(detected_language):
                tess_code = self._get_tesseract_code_from_lang(detected_language)
                if self.is_language_available('en'):
                    strategies.append((f'{tess_code}+eng', '--oem 3 --psm 6'))
                else:
                    strategies.append((tess_code, '--oem 3 --psm 6'))
        
        # Always include English strategies
        if self.is_language_available('en'):
            strategies.extend([
                ('eng', '--oem 3 --psm 6'),   # English, uniform block
                ('eng', '--oem 3 --psm 3'),   # English, fully automatic
            ])
        
        # Add OSD if available (OSD doesn't require specific language files)
        strategies.append(('osd', '--oem 3 --psm 3'))   # Auto script detection
        
        best_text = ""
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
                    # If we get good English text, return early
                    if self.is_likely_english(text):
                        logger.info(f"✅ Good English text found with {lang}")
                        break
            except Exception as e:
                logger.warning(f"English/Auto strategy {lang} failed: {e}")
                continue
        
        return best_text
    
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