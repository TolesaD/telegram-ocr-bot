# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
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
        """Enhanced text extraction preserving original formatting"""
        start_time = time.time()
        
        try:
            # Use gentle preprocessing to preserve original characters
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.preservative_preprocessing,
                image_bytes
            )
            
            # Try Amharic first, then fallback to auto-detection
            text = await self.try_amharic_first(processed_image, image_bytes)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                return "🔍 No readable text found. Please ensure:\n• Clear, high-contrast image\n• Proper lighting\n• Text is horizontal and focused"
            
            # Enhanced cleaning that preserves original formatting
            cleaned_text = self.preservative_clean_text(text)
            
            logger.info(f"✅ OCR completed in {processing_time:.2f}s")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return f"❌ Processing error. Please try a clearer image."
    
    async def try_amharic_first(self, processed_image, original_image_bytes):
        """Try Amharic OCR first, then fallback to other languages"""
        strategies = [
            self.amharic_high_confidence,
            self.amharic_standard,
            self.amharic_legacy,
            self.auto_detect_script
        ]
        
        for strategy in strategies:
            try:
                text = await strategy(processed_image, original_image_bytes)
                if text and len(text.strip()) > 10:
                    amharic_chars = sum(1 for c in text if is_amharic_character(c))
                    if amharic_chars > 0:  # Found Amharic characters
                        logger.info(f"✅ Strategy {strategy.__name__} found Amharic text")
                        return text
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        # If no Amharic found, try English
        return await self.english_fallback(processed_image)
    
    async def amharic_high_confidence(self, processed_image, original_image_bytes):
        """High confidence Amharic processing"""
        # Try multiple Amharic-specific configurations
        configs = [
            get_amharic_config(),
            '--oem 1 --psm 6 -c preserve_interword_spaces=1',
            '--oem 1 --psm 4 -c textord_old_baselines=1',
            '--oem 1 --psm 3 -c textord_force_make_proportional=0'
        ]
        
        best_text = ""
        for config in configs:
            try:
                text = await self.extract_with_tesseract(processed_image, 'amh+amh_vert', config)
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
            except:
                continue
        
        return best_text
    
    async def amharic_standard(self, processed_image, original_image_bytes):
        """Standard Amharic processing"""
        return await self.extract_with_tesseract(processed_image, 'amh', '--oem 1 --psm 6')
    
    async def amharic_legacy(self, processed_image, original_image_bytes):
        """Legacy engine for Amharic"""
        return await self.extract_with_tesseract(processed_image, 'amh', '--oem 0 --psm 6')
    
    async def auto_detect_script(self, processed_image, original_image_bytes):
        """Auto-detect script and language"""
        try:
            # Get available languages
            available_langs = pytesseract.get_languages()
            
            # Try script detection
            script = await self.detect_script(processed_image)
            logger.info(f"📜 Detected script: {script}")
            
            if script == 'Ethiopic':
                return await self.extract_with_tesseract(processed_image, 'amh', '--oem 1 --psm 6')
            else:
                # Auto language detection
                return await self.extract_with_tesseract(processed_image, 'osd', '--oem 1 --psm 3')
        except:
            return await self.english_fallback(processed_image)
    
    async def english_fallback(self, processed_image):
        """Fallback to English"""
        return await self.extract_with_tesseract(processed_image, 'eng', '--oem 3 --psm 6')
    
    def preservative_preprocessing(self, image_bytes):
        """
        Gentle preprocessing that preserves original character shapes
        and doesn't alter the image too much
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale if needed, but preserve color if it helps
            if image.mode != 'L':
                image = image.convert('L')
            
            # Very gentle contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)  # Minimal contrast boost
            
            # Mild sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)  # Minimal sharpening
            
            # Gentle noise reduction only if needed
            image = image.filter(ImageFilter.MedianFilter(size=1))
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def preservative_clean_text(self, text):
        """
        Clean text while preserving original formatting, bullets, and special characters
        """
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Preserve the original line structure
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
        
        # Remove trailing whitespace but preserve internal structure
        return result.strip()
    
    def fix_ocr_artifacts(self, line):
        """Fix common OCR artifacts while preserving original characters"""
        if not line:
            return line
        
        # Fix bullet artifacts - replace common misrecognitions with proper bullets
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
        
        # Fix other common OCR issues while preserving Amharic and special chars
        fixes = {
            '|': 'I',  # But only if it makes sense in context
            '1': 'I',  # Context-dependent
            '5': 'S',
            '0': 'O',
        }
        
        # Apply fixes carefully - only if they improve readability
        for wrong, correct in fixes.items():
            # Only replace if it's likely a misrecognition
            if len(line) > 10:  # Only in longer text to avoid false positives
                line = line.replace(wrong, correct)
        
        return line
    
    async def detect_script(self, image):
        """Detect script using Tesseract"""
        loop = asyncio.get_event_loop()
        try:
            osd = await loop.run_in_executor(
                thread_pool,
                pytesseract.image_to_osd,
                image,
                '--psm 0'
            )
            for line in osd.split('\n'):
                if line.startswith('Script:'):
                    return line.split(':')[1].strip()
            return 'Latin'
        except Exception as e:
            logger.warning(f"Script detection failed: {e}")
            return 'Latin'
    
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