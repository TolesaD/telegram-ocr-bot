# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import get_tesseract_code

logger = logging.getLogger(__name__)

# Set TESSDATA_PREFIX
os.environ['TESSDATA_PREFIX'] = os.getenv('TESSDATA_PREFIX', 'C:\\Program Files\\Tesseract-OCR\\tessdata')

# Enhanced thread pool for better performance
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.engines = {}
        self.cache = {}
        self.setup_engines()
    
    def setup_engines(self):
        """Setup available OCR engines with enhanced error handling"""
        try:
            if self.setup_tesseract():
                self.engines['tesseract'] = {
                    'name': 'Tesseract',
                    'priority': 1,
                    'languages': self.get_tesseract_languages()
                }
            logger.info("🚀 Enhanced OCR Engines loaded: %s", list(self.engines.keys()))
        except Exception as e:
            logger.error("Error setting up OCR engines: %s", e)
    
    def setup_tesseract(self):
        """Setup Tesseract with enhanced configuration"""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized successfully")
            self.tesseract_config = '--oem 3 --psm 1 -c preserve_interword_spaces=1'
            return True
        except Exception as e:
            logger.error("Tesseract initialization failed: %s", e)
            return False
    
    def get_tesseract_languages(self):
        """Get available Tesseract languages with caching"""
        try:
            available_langs = pytesseract.get_languages()
            logger.info("🌍 Available Tesseract languages: %s", available_langs)
            return available_langs
        except Exception as e:
            logger.error("Error getting Tesseract languages: %s", e)
            return ['eng']
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with performance optimizations"""
        start_time = time.time()
        
        try:
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.enhanced_preprocess_image,
                image_bytes
            )
            
            script = await self.detect_script(processed_image)
            logger.info(f"Detected script: {script}")
            
            lang_code = self.get_lang_from_script(script)
            
            available_langs = self.get_tesseract_languages()
            if lang_code not in available_langs:
                logger.warning(f"Language {lang_code} not available, using English")
                lang_code = 'eng'
            
            text = await self.extract_with_tesseract_enhanced(processed_image, lang_code)
            text = self.fix_bullet_artifacts(text)
            
            processing_time = time.time() - start_time
            logger.info("⚡ Tesseract processed in %.2fs", processing_time)
            return text
            
        except Exception as e:
            logger.error("OCR processing failed: {e}")
            return f"❌ OCR failed: {str(e)}. Please ensure the language pack is installed and try a clearer image."
    
    async def detect_script(self, image):
        """Detect script using Tesseract OSD"""
        loop = asyncio.get_event_loop()
        try:
            osd = await loop.run_in_executor(
                thread_pool,
                pytesseract.image_to_osd,
                image
            )
            for line in osd.split('\n'):
                if line.startswith('Script:'):
                    return line.split(':')[1].strip()
            return 'Latin'
        except Exception as e:
            logger.error(f"Script detection failed: {e}")
            return 'Latin'
    
    def get_lang_from_script(self, script):
        """Map script to language code, fallback if not available"""
        mapping = {
            'Latin': 'eng',
            'Cyrillic': 'rus',
            'Arabic': 'ara',
            'Devanagari': 'hin',
            'HanS': 'chi_sim',
            'Hangul': 'kor',
            'Japanese': 'jpn',
            'Tamil': 'tam',
            'Telugu': 'tel',
            'Kannada': 'kan',
            'Malayalam': 'mal',
            'Gujarati': 'guj',
            'Gurmukhi': 'pan',
            'Bengali': 'ben',
            'Amharic': 'amh',
            'Hebrew': 'heb',
            'Armenian': 'hye',
            'Georgian': 'kat',
            'Thai': 'tha',
            'Lao': 'lao',
            'Khmer': 'khm',
            'Myanmar': 'mya',
            'Sinhala': 'sin',
            'Greek': 'ell',
            'Ethiopic': 'amh',
            'Oriya': 'ori',
            'Sindhi': 'snd',
            'Tibetan': 'bod',
            'Swahili': 'swa',
            'Yoruba': 'yor'
        }
        lang_code = mapping.get(script, 'eng')
        available_langs = self.get_tesseract_languages()
        return lang_code if lang_code in available_langs else 'eng'
    
    async def extract_with_tesseract_enhanced(self, image, lang_code):
        """Enhanced Tesseract extraction preserving structure"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_enhanced,
            image,
            lang_code
        )
    
    def _tesseract_extract_enhanced(self, image, lang_code):
        """Extract text with Tesseract, preserving structure"""
        try:
            config = '--oem 3 --psm 1 -c preserve_interword_spaces=1'
            text = pytesseract.image_to_string(
                image,
                lang=lang_code,
                config=config,
                timeout=30
            )
            cleaned_text = self.enhanced_clean_text(text)
            
            if not cleaned_text.strip():
                return "🔍 No readable text found. Please try:\n• Clearer, well-lit images\n• Better focus and contrast\n• Straight, non-blurry photos\n• Crop to text area"
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return f"❌ OCR failed: {str(e)}. Please try again with a clearer image."
    
    def enhanced_preprocess_image(self, image_bytes):
        """Advanced image preprocessing for better OCR accuracy"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_width, original_height = image.size
            
            max_dim = 2000  # Increased for better detail
            if max(image.size) > max_dim:
                scale = max_dim / max(image.size)
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug("🖼️ Resized image from %dx%d to %dx%d", 
                           original_width, original_height, new_width, new_height)
            
            if image.mode != 'L':
                image = image.convert('L')
            
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(3.0)  # Increased for better bullet recognition
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(3.0)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)
            image = image.filter(ImageFilter.MedianFilter(size=3))
            image = image.filter(ImageFilter.EDGE_ENHANCE)
            image = ImageOps.autocontrast(image, cutoff=3)
            
            return image
            
        except Exception as e:
            logger.error("Enhanced preprocessing error: %s", e)
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def enhanced_clean_text(self, text):
        """Advanced text cleaning preserving structure"""
        if not text:
            return ""
        
        lines = text.split('\n')
        filtered_lines = []
        prev_empty = False
        for line in lines:
            stripped = line.lstrip()
            if stripped:
                filtered_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                filtered_lines.append('')
                prev_empty = True
        
        result = '\n'.join(filtered_lines).rstrip()
        if len(result.strip()) < 10:
            return "📝 Very little text detected. Please try:\n• Higher quality image\n• Better lighting conditions\n• Clearer text focus\n• Less complex background"
        
        return result
    
    def fix_bullet_artifacts(self, text):
        """Fix common bullet artifacts like 'e', 'o', or 'point'"""
        lines = text.split('\n')
        fixed_lines = []
        bullet_chars = ['e', 'o', '0', 'point', '•', '*', '-', '–']
        for line in lines:
            stripped = line.strip()
            if stripped:
                for bullet in bullet_chars:
                    if stripped.startswith(bullet + ' ') or stripped == bullet:
                        line = line.replace(bullet, '•', 1)
                        break
            fixed_lines.append(line)
        return '\n'.join(fixed_lines)
    
    def remove_ocr_artifacts(self, text):
        """Remove common OCR artifacts"""
        if len(text) == 1 and not text.isalnum():
            return ""
        replacements = {
            '|': 'I',
            '0': 'O',
            '1': 'I',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

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