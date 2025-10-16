# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from ocr_engine.language_support import get_tesseract_code

logger = logging.getLogger(__name__)

# Enhanced thread pool for better performance
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.engines = {}
        self.cache = {}  # Simple cache for frequent languages
        self.setup_engines()
    
    def setup_engines(self):
        """Setup available OCR engines with enhanced error handling"""
        try:
            # Setup Tesseract with better configuration
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
            # Test if Tesseract works
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized successfully")
            
            # Set optimized Tesseract configuration
            self.tesseract_config = '--oem 3 --psm 3 -c preserve_interword_spaces=1'
            
            return True
        except Exception as e:
            logger.error("Tesseract initialization failed: %s", e)
            return False
    
    def get_tesseract_languages(self):
        """Get available Tesseract languages with caching"""
        try:
            # Get available languages
            available_langs = pytesseract.get_languages()
            logger.info("🌍 Available Tesseract languages: %s", available_langs)
            return available_langs
        except Exception as e:
            logger.error("Error getting Tesseract languages: %s", e)
            return ['eng']
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with performance optimizations and auto script detection"""
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.enhanced_preprocess_image,
                image_bytes
            )
            
            # Detect script
            script = await self.detect_script(processed_image)
            logger.info(f"Detected script: {script}")
            
            lang_code = self.get_lang_from_script(script)
            
            # Check if available
            available_langs = self.get_tesseract_languages()
            if lang_code not in available_langs:
                logger.warning(f"Language {lang_code} not available, using English")
                lang_code = 'eng'
            
            # Extract text preserving structure
            text = await self.extract_with_tesseract_enhanced(processed_image, lang_code)
            
            processing_time = time.time() - start_time
            logger.info("⚡ Tesseract processed in %.2fs", processing_time)
            return text
            
        except Exception as e:
            logger.error("OCR processing failed: %s", e)
            raise
    
    async def detect_script(self, image):
        loop = asyncio.get_event_loop()
        osd = await loop.run_in_executor(
            thread_pool,
            pytesseract.image_to_osd,
            image
        )
        for line in osd.split('\n'):
            if line.startswith('Script:'):
                return line.split(':')[1].strip()
        return 'Latin'
    
    def get_lang_from_script(self, script):
        mapping = {
            'Latin': 'eng',
            'Cyrillic': 'rus',
            'Arabic': 'ara',
            'Devanagari': 'hin',
            'HanS': 'chi_sim',  # Simplified Chinese
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
            # Add more as needed for 100 languages
            'Armenian': 'hye',
            'Georgian': 'kat',
            'Thai': 'tha',
            'Lao': 'lao',
            'Khmer': 'khm',
            'Myanmar': 'mya',
            'Sinhala': 'sin',
            'Greek': 'ell',
            'Ethiopic': 'amh',  # For African like Amharic
            # etc.
        }
        return mapping.get(script, 'eng')
    
    async def extract_with_tesseract_enhanced(self, image, lang_code):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_enhanced,
            image,
            lang_code
        )
    
    def _tesseract_extract_enhanced(self, image, lang_code):
        """Enhanced Tesseract extraction preserving structure"""
        try:
            # Use PSM 3 for full page segmentation to preserve layout
            config = '--oem 3 --psm 3 -c preserve_interword_spaces=1'
            
            text = pytesseract.image_to_string(
                image,
                lang=lang_code,
                config=config,
                timeout=30
            )
            
            cleaned_text = self.enhanced_clean_text(text)
            
            if not cleaned_text:
                return "🔍 No readable text found. Please try:\n• Clearer, well-lit images\n• Better focus and contrast\n• Straight, non-blurry photos\n• Crop to text area"
            
            return cleaned_text
            
        except Exception as e:
            raise Exception(f"Tesseract error: {e}")
    
    def enhanced_preprocess_image(self, image_bytes):
        """Advanced image preprocessing for better OCR accuracy"""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Store original dimensions
            original_width, original_height = image.size
            
            # Optimize image size for OCR (better performance/accuracy balance)
            max_dim = 1600  # Increased for better detail
            if max(image.size) > max_dim:
                scale = max_dim / max(image.size)
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug("🖼️ Resized image from %dx%d to %dx%d", 
                           original_width, original_height, new_width, new_height)
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Multiple enhancement techniques
            # 1. Contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.5)  # Increased contrast
            
            # 2. Sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.5)  # Increased sharpness
            
            # 3. Brightness adjustment
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # 4. Noise reduction with multiple techniques
            image = image.filter(ImageFilter.MedianFilter(size=3))
            image = image.filter(ImageFilter.SMOOTH)
            
            # 5. Edge enhancement for text boundaries
            image = image.filter(ImageFilter.EDGE_ENHANCE)
            
            # 6. Auto contrast for better text visibility
            image = ImageOps.autocontrast(image, cutoff=2)
            
            return image
            
        except Exception as e:
            logger.error("Enhanced preprocessing error: %s", e)
            # Fallback to basic processing
            try:
                image = Image.open(io.BytesIO(image_bytes))
                if image.mode != 'L':
                    image = image.convert('L')
                return image
            except:
                return Image.open(io.BytesIO(image_bytes))
    
    def enhanced_clean_text(self, text):
        """Advanced text cleaning preserving structure"""
        if not text:
            return ""
        
        # Preserve lines, remove excessive empty lines
        lines = text.split('\n')
        filtered_lines = []
        prev_empty = False
        for line in lines:
            stripped = line.strip()
            if stripped:
                filtered_lines.append(line.rstrip())  # Preserve leading spaces for indents/lists
                prev_empty = False
            elif not prev_empty:
                filtered_lines.append('')
                prev_empty = True
        
        # Join back
        result = '\n'.join(filtered_lines).rstrip()
        
        # Final validation
        if len(result.strip()) < 10:
            return "📝 Very little text detected. Please try:\n• Higher quality image\n• Better lighting conditions\n• Clearer text focus\n• Less complex background"
        
        return result
    
    def remove_ocr_artifacts(self, text):
        """Remove common OCR artifacts and noise"""
        # Remove single character lines that are likely noise
        if len(text) == 1 and not text.isalnum():
            return ""
        
        # Remove common OCR mistakes
        replacements = {
            '|': 'I',
            '0': 'O',  # in some fonts
            '1': 'I',  # in some contexts
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text

# Global instance
ocr_processor = OCRProcessor()

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times = []
    
    def record_request(self, processing_time):
        self.request_times.append(processing_time)
        # Keep only last 100 records
        if len(self.request_times) > 100:
            self.request_times.pop(0)
    
    def get_stats(self):
        if not self.request_times:
            return "No requests yet"
        avg_time = sum(self.request_times) / len(self.request_times)
        return f"Average processing time: {avg_time:.2f}s"

performance_monitor = PerformanceMonitor()