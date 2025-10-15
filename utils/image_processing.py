import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
thread_pool = ThreadPoolExecutor(max_workers=3)

class OCRProcessor:
    def __init__(self):
        self.engines = {}
        self.setup_engines()
    
    def setup_engines(self):
        """Setup available OCR engines"""
        try:
            # Setup Tesseract (Primary)
            if self.setup_tesseract():
                self.engines['tesseract'] = {
                    'name': 'Tesseract',
                    'priority': 1,
                    'languages': self.get_tesseract_languages()
                }
            
            logger.info("OCR Engines loaded: %s", list(self.engines.keys()))
            
        except Exception as e:
            logger.error("Error setting up OCR engines: %s", e)
    
    def setup_tesseract(self):
        """Setup Tesseract"""
        try:
            # Test if Tesseract works
            pytesseract.get_tesseract_version()
            logger.info("Tesseract initialized successfully")
            return True
        except Exception as e:
            logger.error("Tesseract initialization failed: %s", e)
            return False
    
    def get_tesseract_languages(self):
        """Get available Tesseract languages"""
        try:
            # Get available languages
            available_langs = pytesseract.get_languages()
            logger.info("Available Tesseract languages: %s", available_langs)
            return available_langs
        except Exception as e:
            logger.error("Error getting Tesseract languages: %s", e)
            return ['eng']
    
    async def extract_text_optimized(self, image_bytes, language='english'):
        """Extract text using Tesseract"""
        start_time = time.time()
        
        try:
            # Convert language name to code
            lang_code = self.get_language_code(language)
            logger.info("Using language: %s -> %s", language, lang_code)
            
            # Use Tesseract
            text = await self.extract_with_tesseract(image_bytes, lang_code)
            
            processing_time = time.time() - start_time
            logger.info("Tesseract succeeded in %.2fs", processing_time)
            return text
            
        except Exception as e:
            logger.error("OCR processing failed: %s", e)
            raise
    
    def get_language_code(self, language_name):
        """Convert language name to Tesseract code"""
        language_map = {
            'english': 'eng',
            'spanish': 'spa', 
            'french': 'fra',
            'german': 'deu',
            'italian': 'ita',
            'portuguese': 'por',
            'russian': 'rus',
            'chinese_simplified': 'chi_sim',
            'japanese': 'jpn',
            'korean': 'kor',
            'arabic': 'ara',
            'hindi': 'hin',
            'turkish': 'tur',
            'dutch': 'nld',
            'swedish': 'swe',
            'polish': 'pol',
            'ukrainian': 'ukr',
            'greek': 'ell',
            'amharic': 'amh',
        }
        
        return language_map.get(language_name.lower(), 'eng')
    
    async def extract_with_tesseract(self, image_bytes, lang_code):
        """Extract text with Tesseract"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract,
            image_bytes,
            lang_code
        )
    
    def _tesseract_extract(self, image_bytes, lang_code):
        """Tesseract extraction in thread"""
        try:
            # Preprocess image using PIL only (no OpenCV)
            processed_image = self.preprocess_image_pil(image_bytes)
            
            # Check if language is available
            available_langs = self.get_tesseract_languages()
            if lang_code not in available_langs:
                logger.warning("Language %s not available, using English", lang_code)
                lang_code = 'eng'
            
            # Try different page segmentation modes
            psm_modes = [6, 3, 4, 8, 11]
            
            for psm_mode in psm_modes:
                try:
                    config = f'--oem 3 --psm {psm_mode}'
                    text = pytesseract.image_to_string(
                        processed_image,
                        lang=lang_code,
                        config=config,
                        timeout=30
                    )
                    
                    cleaned_text = self.clean_text(text)
                    
                    # If we got reasonable text, use it
                    if cleaned_text and len(cleaned_text.strip()) > 10:
                        logger.info("PSM mode %d successful", psm_mode)
                        return cleaned_text
                        
                except Exception as e:
                    logger.warning("PSM mode %d failed: %s", psm_mode, str(e))
                    continue
            
            # If all PSM modes failed, try one more time with default
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang_code,
                timeout=30
            )
            
            cleaned_text = self.clean_text(text)
            
            if not cleaned_text:
                return "No readable text found. Please try:\n• Clearer image\n• Better lighting\n• Straight photo\n• High contrast"
            
            return cleaned_text
            
        except Exception as e:
            raise Exception(f"Tesseract error: {e}")
    
    def preprocess_image_pil(self, image_bytes):
        """Image preprocessing using only PIL (no OpenCV)"""
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize if too large (better for OCR accuracy)
            max_dim = 1200
            if max(image.size) > max_dim:
                scale = max_dim / max(image.size)
                new_width = int(image.width * scale)
                new_height = int(image.height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply mild filter to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            logger.error("PIL preprocessing error: %s", e)
            # Fallback to simple processing
            try:
                image = Image.open(io.BytesIO(image_bytes))
                if image.mode != 'L':
                    image = image.convert('L')
                return image
            except:
                return Image.open(io.BytesIO(image_bytes))
    
    def clean_text(self, text):
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Filter out lines that are too short or don't contain text
        filtered_lines = []
        for line in lines:
            # Keep lines with meaningful content
            if len(line) > 1:
                # Check if line contains letters or numbers
                has_text = any(c.isalnum() for c in line)
                if has_text:
                    filtered_lines.append(line)
        
        result = '\n'.join(filtered_lines)
        
        # If result is too short, return a helpful message
        if len(result.strip()) < 10:
            return "Very little text detected. Please try a clearer image with more visible text."
        
        return result

# Global instance
ocr_processor = OCRProcessor()