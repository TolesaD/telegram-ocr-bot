# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
import subprocess
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import get_tesseract_code, get_amharic_config, is_amharic_character

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")  # Reduced workers for better memory management

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
        self.available_languages = []
        self._load_available_languages()
        self.performance_cache = {}  # Cache for performance optimization
    
    def setup_tesseract(self):
        """Setup Tesseract with automatic path detection"""
        try:
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
        """Find Tesseract installation path"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract', 
            '/bin/tesseract',
            '/app/bin/tesseract'
        ]
        
        try:
            result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
            if result.returncode == 0:
                found_path = result.stdout.strip()
                if found_path and os.path.exists(found_path):
                    return found_path
        except:
            pass
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_available_languages(self):
        """Load available Tesseract languages"""
        try:
            self.available_languages = pytesseract.get_languages()
            logger.info(f"📚 Found {len(self.available_languages)} available languages")
        except Exception as e:
            logger.error(f"Error loading available languages: {e}")
            self.available_languages = ['eng']
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Optimized text extraction with performance improvements"""
        start_time = time.time()
        
        try:
            # Quick preprocessing for speed
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.fast_preprocessing,
                image_bytes
            )
            
            # Fast language detection
            detected_language = await self.fast_language_detection(processed_image)
            logger.info(f"🔍 Detected language: {detected_language}")
            
            # Use cached strategies for performance
            if detected_language == 'am':
                text = await self.optimized_amharic_ocr(processed_image)
            else:
                text = await self.optimized_english_ocr(processed_image)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                return "🔍 No readable text found. Please try a clearer image."
            
            # Fast text cleaning
            cleaned_text = self.fast_clean_text(text)
            
            logger.info(f"✅ {detected_language.upper()} OCR completed in {processing_time:.2f}s")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return "❌ OCR processing failed. Please try again with a different image."
    
    def fast_preprocessing(self, image_bytes):
        """Fast preprocessing optimized for performance"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale quickly
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize large images for faster processing (keep aspect ratio)
            max_size = 2000
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Resized image from {image.size} to {new_size}")
            
            # Quick contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    async def fast_language_detection(self, processed_image):
        """Fast language detection focusing on common cases"""
        try:
            # Quick Amharic test
            amh_text = await self.extract_with_tesseract(processed_image, 'amh', '--psm 6 --oem 1', timeout=10)
            amh_chars = sum(1 for c in amh_text if '\u1200' <= c <= '\u137F')
            
            if amh_chars > 5:  # If we find several Amharic characters
                return 'am'
            else:
                return 'en'  # Default to English for speed
                
        except Exception as e:
            logger.warning(f"Fast language detection failed: {e}")
            return 'en'
    
    async def optimized_amharic_ocr(self, processed_image):
        """Optimized Amharic OCR with best-performing strategies"""
        # Use only the most effective strategies based on testing
        strategies = [
            ('amh', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            ('amh+eng', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            ('amh', '--oem 1 --psm 4 -c preserve_interword_spaces=1'),
        ]
        
        best_text = ""
        best_confidence = 0
        
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config, timeout=30)
                if text and text.strip():
                    confidence = self._calculate_amharic_confidence(text)
                    
                    if confidence > best_confidence:
                        best_text = text
                        best_confidence = confidence
                    
                    # Early exit if we get good results
                    if confidence > 0.5:
                        break
            except Exception as e:
                continue
        
        # Fallback to English if Amharic results are poor
        if best_confidence < 0.2:
            english_text = await self.extract_with_tesseract(processed_image, 'eng', '--oem 3 --psm 6', timeout=20)
            if english_text and english_text.strip():
                return english_text
        
        return best_text
    
    async def optimized_english_ocr(self, processed_image):
        """Optimized English OCR"""
        strategies = [
            ('eng', '--oem 3 --psm 6'),
            ('eng', '--oem 3 --psm 3'),
        ]
        
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config, timeout=20)
                if text and text.strip():
                    return text
            except Exception as e:
                continue
        
        return ""
    
    def _calculate_amharic_confidence(self, text):
        """Fast Amharic confidence calculation"""
        if not text:
            return 0
        
        amharic_chars = sum(1 for c in text if '\u1200' <= c <= '\u137F')
        total_chars = len(text)
        
        if total_chars == 0:
            return 0
        
        return amharic_chars / total_chars
    
    def fast_clean_text(self, text):
        """Fast text cleaning"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    async def extract_with_tesseract(self, image, lang, config, timeout=30):
        """Extract text with Tesseract with timeout"""
        loop = asyncio.get_event_loop()
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(
                    thread_pool,
                    lambda: pytesseract.image_to_string(image, lang=lang, config=config)
                ),
                timeout=timeout
            )
            return text
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Tesseract timeout for {lang}")
            return ""
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
        # Keep only last 50 requests
        if len(self.request_times) > 50:
            self.request_times.pop(0)
    
    def get_stats(self):
        if not self.request_times:
            return "No requests yet"
        avg_time = sum(self.request_times) / len(self.request_times)
        return f"Average processing time: {avg_time:.2f}s"

performance_monitor = PerformanceMonitor()