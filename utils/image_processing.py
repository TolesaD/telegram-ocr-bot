import asyncio
import logging
import time
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor

# Set Tesseract path for Windows
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
thread_pool = ThreadPoolExecutor(max_workers=3)

class OCRProcessor:
    def __init__(self):
        self.engines = {}
        self.setup_engines()
    
    def setup_engines(self):
        """Setup available OCR engines with fallback"""
        try:
            # Setup Tesseract (Primary)
            if self.setup_tesseract():
                self.engines['tesseract'] = {
                    'name': 'Tesseract',
                    'priority': 1,
                    'languages': self.get_tesseract_languages()
                }
            
            # Try to setup PaddleOCR (Optional - will be skipped if not installed)
            if self.setup_paddle_ocr():
                self.engines['paddle_ocr'] = {
                    'name': 'PaddleOCR',
                    'priority': 2,
                    'languages': ['en', 'ch', 'fr', 'de', 'es', 'it', 'pt', 'ru', 'ja', 'ko', 'ar', 'hi']
                }
            else:
                logger.warning("PaddleOCR not available, using Tesseract only")
            
            logger.info("OCR Engines loaded: %s", list(self.engines.keys()))
            
        except Exception as e:
            logger.error("Error setting up OCR engines: %s", e)
    
    def setup_tesseract(self):
        """Setup Tesseract path"""
        try:
            # Test if Tesseract works
            pytesseract.get_tesseract_version()
            logger.info("Tesseract initialized successfully")
            return True
        except Exception as e:
            logger.error("Tesseract initialization failed: %s", e)
            return False
    
    def setup_paddle_ocr(self):
        """Setup PaddleOCR with graceful fallback"""
        try:
            import paddleocr
            self.paddle_ocr = paddleocr.PaddleOCR(
                use_angle_cls=True,
                lang='en',
                show_log=False,
                use_gpu=False
            )
            logger.info("PaddleOCR initialized")
            return True
        except ImportError:
            logger.warning("PaddleOCR not installed. Install with: pip install paddleocr")
            return False
        except Exception as e:
            logger.warning("PaddleOCR initialization failed: %s", e)
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
        """Extract text using best available engine"""
        start_time = time.time()
        
        try:
            # Convert language name to code
            lang_code = self.get_language_code(language)
            logger.info("Using language: %s -> %s", language, lang_code)
            
            # Try engines in priority order
            engines_to_try = sorted(
                self.engines.items(),
                key=lambda x: x[1]['priority']
            )
            
            last_error = None
            for engine_name, engine_info in engines_to_try:
                try:
                    logger.info("Trying %s for %s (%s)", engine_name, language, lang_code)
                    
                    if engine_name == 'paddle_ocr':
                        text = await self.extract_with_paddle_ocr(image_bytes, lang_code)
                    elif engine_name == 'tesseract':
                        text = await self.extract_with_tesseract(image_bytes, lang_code)
                    else:
                        continue
                    
                    if text and len(text.strip()) > 5:  # Valid text found
                        processing_time = time.time() - start_time
                        logger.info("%s succeeded in %.2fs", engine_name, processing_time)
                        return text
                        
                except Exception as e:
                    last_error = e
                    logger.warning("%s failed: %s", engine_name, str(e))
                    continue
            
            # All engines failed
            error_msg = f"All OCR engines failed for {language}"
            if last_error:
                error_msg += f". Last error: {last_error}"
            raise Exception(error_msg)
            
        except Exception as e:
            logger.error("OCR processing failed: %s", e)
            raise
    
    def get_language_code(self, language_name):
        """Convert language name to Tesseract code"""
        # Simple language mapping
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
        }
        
        # Default to English if language not found
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
            # Preprocess image
            processed_image = self.fast_preprocess_image(image_bytes)
            
            # Check if language is available
            available_langs = self.get_tesseract_languages()
            if lang_code not in available_langs:
                logger.warning("Language %s not available, using English", lang_code)
                lang_code = 'eng'
            
            # Try different page segmentation modes if default fails
            psm_modes = [6, 3, 4, 8, 11]  # Try different modes
            
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
    
    async def extract_with_paddle_ocr(self, image_bytes, lang_code):
        """Extract text with PaddleOCR (if available)"""
        if not hasattr(self, 'paddle_ocr'):
            raise Exception("PaddleOCR not available")
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._paddle_extract,
            image_bytes,
            lang_code
        )
    
    def _paddle_extract(self, image_bytes, lang_code):
        """PaddleOCR extraction in thread"""
        try:
            # Convert to numpy array for OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise Exception("Failed to decode image")
            
            # Run OCR
            result = self.paddle_ocr.ocr(img, cls=True)
            
            if not result or not result[0]:
                return "No text detected in the image."
            
            # Combine all detected text
            texts = []
            for line in result[0]:
                if line and len(line) >= 2:
                    texts.append(line[1][0])
            
            cleaned_text = self.clean_text('\n'.join(texts))
            
            if not cleaned_text:
                return "No readable text found."
            
            return cleaned_text
            
        except Exception as e:
            raise Exception(f"PaddleOCR error: {e}")
    
    def fast_preprocess_image(self, image_bytes):
        """Fast image preprocessing with OpenCV"""
        try:
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                # Fallback to PIL if OpenCV fails
                return Image.open(io.BytesIO(image_bytes))
            
            # Resize if too large (better for OCR accuracy)
            height, width = img.shape[:2]
            max_dim = 1200  # Reduced for better performance
            if max(height, width) > max_dim:
                scale = max_dim / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Convert to grayscale
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply mild Gaussian blur to reduce noise
            img = cv2.GaussianBlur(img, (1, 1), 0)
            
            # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img = clahe.apply(img)
            
            # Apply threshold to get binary image
            _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL for Tesseract
            pil_img = Image.fromarray(img)
            return pil_img
            
        except Exception as e:
            logger.error("Preprocessing error: %s", e)
            # Fallback to simple PIL processing
            try:
                image = Image.open(io.BytesIO(image_bytes))
                # Simple preprocessing
                if image.mode != 'L':
                    image = image.convert('L')
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)  # Increase contrast
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

# Backward compatibility
class ImageProcessor:
    @staticmethod
    async def extract_text_async(image_bytes, language='eng'):
        """Backward compatibility method"""
        return await ocr_processor.extract_text_optimized(image_bytes, 'english')