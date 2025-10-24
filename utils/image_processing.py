# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
        self.available_languages = []
        self._load_available_languages()
    
    def setup_tesseract(self):
        """Setup Tesseract with automatic path detection"""
        try:
            # Try to find Tesseract automatically
            tesseract_path = self._find_tesseract()
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                logger.info(f"✅ Tesseract found at: {tesseract_path}")
            else:
                logger.error("❌ Could not find Tesseract installation")
                return False
            
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            return False

    def _find_tesseract(self):
        """Find Tesseract installation path with better detection"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract', 
            '/bin/tesseract',
            '/app/bin/tesseract',
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',  # Windows
            'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',  # Windows 32-bit
        ]
        
        # First try system PATH
        try:
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                logger.info(f"🔍 Found Tesseract via PATH: {tesseract_path}")
                return tesseract_path
        except:
            pass
        
        # Try Windows registry
        try:
            if os.name == 'nt':  # Windows
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR")
                    tesseract_path = winreg.QueryValueEx(key, "InstallDir")[0] + "\\tesseract.exe"
                    winreg.CloseKey(key)
                    if os.path.exists(tesseract_path):
                        logger.info(f"🔍 Found Tesseract via Registry: {tesseract_path}")
                        return tesseract_path
                except:
                    pass
        except:
            pass
        
        # Check possible paths
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"🔍 Found Tesseract at: {path}")
                return path
        
        logger.error("❌ Could not find Tesseract in any known location")
        return None

    def _load_available_languages(self):
        """Load available Tesseract languages"""
        try:
            # Get languages using pytesseract
            langs_output = subprocess.run([
                pytesseract.pytesseract.tesseract_cmd, '--list-langs'
            ], capture_output=True, text=True, timeout=10)
            
            if langs_output.returncode == 0:
                # Parse the output to get language list
                lines = langs_output.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Skip the first line ("List of available languages:")
                    self.available_languages = lines[1:]
                else:
                    self.available_languages = ['eng']  # Default fallback
            else:
                self.available_languages = ['eng']  # Default fallback
                
            logger.info(f"📚 Found {len(self.available_languages)} available languages: {self.available_languages}")
            
            # Specifically check for Amharic
            if 'amh' in self.available_languages:
                logger.info("✅ Amharic language is available")
            else:
                logger.warning("❌ Amharic language is NOT available")
                
        except Exception as e:
            logger.error(f"Error loading available languages: {e}")
            self.available_languages = ['eng']

    def is_language_available(self, lang_code):
        """Check if a language is available"""
        # Simple mapping for common languages
        lang_mapping = {
            'en': 'eng',
            'am': 'amh', 
            'ar': 'ara',
            'es': 'spa',
            'fr': 'fra',
            'de': 'deu',
            'ru': 'rus',
            'zh': 'chi_sim',
            'ja': 'jpn',
            'ko': 'kor'
        }
        tesseract_code = lang_mapping.get(lang_code, lang_code)
        return tesseract_code in self.available_languages

    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with comprehensive Amharic support"""
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
            if detected_language == 'am':
                logger.info("🎯 Using Amharic OCR strategy")
                text = await self.comprehensive_amharic_ocr(processed_image)
            else:
                logger.info("🎯 Using English OCR strategy")
                text = await self.english_or_auto_ocr(processed_image, detected_language)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                logger.warning("❌ No text extracted or text too short")
                return "🔍 No readable text found. Please try a clearer image."
            
            # Minimal cleaning to preserve all characters
            cleaned_text = self._minimal_clean_text(text)
            
            logger.info(f"✅ {detected_language.upper()} OCR completed in {processing_time:.2f}s")
            logger.info(f"📝 Extracted {len(cleaned_text)} characters")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            logger.error(f"Full error details:", exc_info=True)
            return "❌ OCR processing failed. Please try again with a different image."

    async def detect_language_smart(self, processed_image):
        """Language detection focusing on Amharic with better logic"""
        try:
            # Quick test with Amharic first
            amh_text = await self.extract_with_tesseract(processed_image, 'amh', '--psm 6 --oem 1')
            amh_confidence = self._calculate_amharic_confidence(amh_text)
            
            # Test English
            eng_text = await self.extract_with_tesseract(processed_image, 'eng', '--psm 6 --oem 1')
            eng_latin_chars = sum(1 for c in eng_text if c.isalpha() and c.isascii())
            eng_total_chars = len(eng_text.strip())
            eng_confidence = eng_latin_chars / eng_total_chars if eng_total_chars > 0 else 0
            
            logger.info(f"🔍 Language detection - Amharic: {amh_confidence:.2f}, English: {eng_confidence:.2f}")
            
            # Improved logic: Choose language with highest confidence
            # But require minimum confidence for Amharic to avoid false positives
            if amh_confidence > 0.5:  # Strong Amharic signal
                return 'am'
            elif eng_confidence > 0.6:  # Strong English signal
                return 'en'
            elif eng_confidence > amh_confidence:  # English is more likely
                return 'en'
            else:
                return 'en'  # Default to English for safety
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'en'

    def _calculate_amharic_confidence(self, text):
        """More accurate Amharic confidence calculation"""
        if not text or not text.strip():
            return 0
        
        text = text.strip()
        total_chars = len(text)
        
        if total_chars == 0:
            return 0
        
        # Count Amharic characters (Ethiopic Unicode range)
        amharic_chars = sum(1 for c in text if '\u1200' <= c <= '\u137F')
        
        # Also count common Amharic punctuation and numbers
        amharic_punctuation = sum(1 for c in text if c in '፡።፣፤፥፦፧፨')
        amharic_numbers = sum(1 for c in text if '\u1369' <= c <= '\u137C')
        
        total_amharic = amharic_chars + amharic_punctuation + amharic_numbers
        
        # Calculate confidence, but give more weight to actual Amharic characters
        confidence = total_amharic / total_chars
        
        # If we have very few characters but they're all Amharic, still consider it
        if total_chars < 10 and amharic_chars > 0:
            confidence = max(confidence, 0.3)
        
        return confidence

    async def comprehensive_amharic_ocr(self, processed_image):
        """Comprehensive Amharic OCR with multiple strategies and fallbacks"""
        strategies = [
            ('amh', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            ('amh', '--oem 1 --psm 4 -c preserve_interword_spaces=1'),
            ('amh+eng', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
        ]
        
        best_text = ""
        best_confidence = 0
        
        for i, (lang, config) in enumerate(strategies):
            try:
                logger.info(f"🔧 Trying Amharic strategy {i+1}: {lang} with {config}")
                text = await self.extract_with_tesseract(processed_image, lang, config)
                
                if text and text.strip():
                    confidence = self._calculate_amharic_confidence(text)
                    
                    if confidence > best_confidence:
                        best_text = text
                        best_confidence = confidence
                    
                    # Early exit if we get good results
                    if confidence > 0.3:
                        logger.info(f"✅ High confidence Amharic text found with {lang}")
                        break
            except Exception as e:
                logger.warning(f"❌ Strategy {i+1} failed: {e}")
                continue
        
        # Fallback to English if Amharic results are poor
        if best_confidence < 0.2:
            english_text = await self.extract_with_tesseract(processed_image, 'eng', '--oem 3 --psm 6')
            if english_text and english_text.strip():
                logger.info("🔄 Falling back to English OCR")
                return english_text
        
        return best_text

    async def _fallback_english_ocr(self, processed_image):
        """Fallback to English OCR"""
        logger.info("🔄 Falling back to English OCR")
        try:
            text = await self.extract_with_tesseract(processed_image, 'eng', '--oem 3 --psm 6')
            if text and text.strip():
                logger.info("✅ English fallback successful")
                return text
        except Exception as e:
            logger.error(f"❌ English fallback also failed: {e}")
        
        return ""

    def _minimal_clean_text(self, text):
        """Minimal text cleaning that preserves all characters"""
        if not text:
            return ""
        
        # Simply normalize whitespace without removing any characters
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove excessive internal whitespace but preserve the line
            cleaned_line = ' '.join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        result = '\n'.join(cleaned_lines)
        return result

    async def english_or_auto_ocr(self, processed_image, detected_language):
        """OCR for English and other languages"""
        strategies = [
            ('eng', '--oem 3 --psm 6'),
            ('eng', '--oem 3 --psm 3'),
            ('eng', '--oem 3 --psm 4'),
        ]
        
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and text.strip():
                    logger.info(f"✅ English OCR successful with config: {config}")
                    return text
            except Exception as e:
                logger.warning(f"English strategy failed: {e}")
                continue
        
        logger.error("❌ All English OCR strategies failed")
        return ""

    def preservative_preprocessing(self, image_bytes):
        """Gentle preprocessing"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode != 'L':
                image = image.convert('L')
            
            # Very gentle enhancements
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')

    async def extract_with_tesseract(self, image, lang, config):
        """Extract text with Tesseract"""
        loop = asyncio.get_event_loop()
        try:
            text = await loop.run_in_executor(
                thread_pool,
                lambda: pytesseract.image_to_string(image, lang=lang, config=config, timeout=60)
            )
            return text
        except Exception as e:
            logger.error(f"Tesseract extraction failed for {lang}: {e}")
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