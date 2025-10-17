# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import get_tesseract_code, get_language_family, is_complex_script

# Try to import OpenCV, but fall back to PIL if not available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ OpenCV loaded successfully")
except ImportError as e:
    OPENCV_AVAILABLE = False
    logger.warning(f"⚠️ OpenCV not available: {e}. Using PIL fallback.")
    # Create dummy numpy if OpenCV fails
    try:
        import numpy as np
    except ImportError:
        np = None

logger = logging.getLogger(__name__)

# Set TESSDATA_PREFIX
os.environ['TESSDATA_PREFIX'] = os.getenv('TESSDATA_PREFIX', 'C:\\Program Files\\Tesseract-OCR\\tessdata')

# Enhanced thread pool for better performance
thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ocr_")

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
            self.tesseract_config = '--oem 3 --psm 3 -c preserve_interword_spaces=1'
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
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
        """Enhanced text extraction with multiple strategies for blurry images and Amharic"""
        start_time = time.time()
        
        try:
            # Strategy 1: Try with enhanced preprocessing for blurry images
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.enhanced_preprocess_image,
                image_bytes
            )
            
            # Strategy 2: Auto-detect script and language
            script = await self.detect_script(processed_image)
            logger.info(f"Detected script: {script}")
            
            # Strategy 3: Try multiple language combinations for Amharic
            lang_code = self.get_lang_from_script(script)
            
            # Enhanced Amharic detection and processing
            if script == 'Ethiopic' or 'amh' in str(script).lower():
                lang_code = 'am'
                logger.info("🔍 Detected Amharic/Ethiopic script, using enhanced Amharic processing")
            
            available_langs = self.get_tesseract_languages()
            
            # Strategy 4: Try multiple OCR attempts with different configurations
            text = await self.multi_strategy_ocr(processed_image, lang_code, available_langs, image_bytes)
            
            processing_time = time.time() - start_time
            logger.info("⚡ Enhanced OCR processed in %.2fs", processing_time)
            
            return text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return f"❌ OCR failed: {str(e)}. Please ensure the language pack is installed and try a clearer image."
    
    async def multi_strategy_ocr(self, processed_image, lang_code, available_langs, original_image_bytes):
        """Try multiple OCR strategies for better accuracy"""
        strategies = [
            self.strategy_standard_ocr,
            self.strategy_enhanced_amharic,
            self.strategy_blurry_image,
            self.strategy_fallback_english
        ]
        
        best_result = ""
        best_confidence = 0
        
        for strategy in strategies:
            try:
                result, confidence = await strategy(processed_image, lang_code, available_langs, original_image_bytes)
                if confidence > best_confidence and len(result.strip()) > 10:
                    best_result = result
                    best_confidence = confidence
                    logger.info(f"✅ Strategy {strategy.__name__} achieved confidence: {confidence}")
                    
                    # If we get good confidence, return early
                    if confidence > 70:
                        break
            except Exception as e:
                logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        if best_result and len(best_result.strip()) > 5:
            return self.fix_bullet_artifacts(best_result)
        else:
            return "🔍 No readable text found. Please try a clearer, well-lit image with focused text."
    
    async def strategy_standard_ocr(self, image, lang_code, available_langs, original_image_bytes):
        """Standard OCR strategy"""
        tesseract_lang = get_tesseract_code(lang_code)
        if tesseract_lang not in available_langs:
            tesseract_lang = 'eng'
        
        text = await self.extract_with_tesseract_enhanced(image, tesseract_lang, 'standard')
        confidence = self.estimate_confidence(text)
        return text, confidence
    
    async def strategy_enhanced_amharic(self, image, lang_code, available_langs, original_image_bytes):
        """Enhanced Amharic OCR strategy"""
        if lang_code != 'am' and 'amh' not in str(get_tesseract_code(lang_code)):
            return "", 0
        
        # Special preprocessing for Amharic
        amharic_image = await asyncio.get_event_loop().run_in_executor(
            thread_pool,
            self.preprocess_for_amharic,
            original_image_bytes
        )
        
        # Try multiple Amharic configurations
        amh_configs = [
            '--oem 1 --psm 6',  # Uniform text block
            '--oem 1 --psm 4',  # Single column
            '--oem 1 --psm 3',  # Fully automatic
        ]
        
        best_text = ""
        for config in amh_configs:
            try:
                text = await self.extract_with_tesseract_custom(amharic_image, 'amh+amh_vert', config)
                if len(text.strip()) > len(best_text.strip()):
                    best_text = text
            except:
                continue
        
        confidence = self.estimate_confidence(best_text)
        return best_text, confidence
    
    async def strategy_blurry_image(self, image, lang_code, available_langs, original_image_bytes):
        """Special strategy for blurry images"""
        blurry_image = await asyncio.get_event_loop().run_in_executor(
            thread_pool,
            self.enhanced_deblur_processing,
            original_image_bytes
        )
        
        tesseract_lang = get_tesseract_code(lang_code)
        if tesseract_lang not in available_langs:
            tesseract_lang = 'eng'
        
        text = await self.extract_with_tesseract_enhanced(blurry_image, tesseract_lang, 'blurry')
        confidence = self.estimate_confidence(text)
        return text, confidence
    
    async def strategy_fallback_english(self, image, lang_code, available_langs, original_image_bytes):
        """Fallback to English if other strategies fail"""
        text = await self.extract_with_tesseract_enhanced(image, 'eng', 'fallback')
        confidence = self.estimate_confidence(text)
        return text, confidence
    
    def estimate_confidence(self, text):
        """Estimate confidence based on text quality"""
        if not text or len(text.strip()) < 5:
            return 0
        
        # Count readable characters vs garbage
        readable_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in ',.!?;:-()[]{}')
        total_chars = len(text)
        
        if total_chars == 0:
            return 0
        
        confidence = (readable_chars / total_chars) * 100
        return min(confidence, 100)
    
    async def detect_script(self, image):
        """Enhanced script detection using Tesseract OSD"""
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
        """Map script to language code with enhanced detection"""
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
            'Ethiopic': 'amh',
            'Hebrew': 'heb',
            'Armenian': 'hye',
            'Georgian': 'kat',
            'Thai': 'tha',
            'Lao': 'lao',
            'Khmer': 'khm',
            'Myanmar': 'mya',
            'Sinhala': 'sin',
            'Greek': 'ell',
            'Oriya': 'ori',
            'Sindhi': 'snd',
            'Tibetan': 'bod'
        }
        lang_code = mapping.get(script, 'eng')
        return lang_code
    
    async def extract_with_tesseract_enhanced(self, image, lang_code, strategy='standard'):
        """Enhanced Tesseract extraction with strategy-based configurations"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_enhanced,
            image,
            lang_code,
            strategy
        )
    
    async def extract_with_tesseract_custom(self, image, lang_code, custom_config):
        """Custom Tesseract extraction with specific configuration"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_custom,
            image,
            lang_code,
            custom_config
        )
    
    def _tesseract_extract_enhanced(self, image, lang_code, strategy):
        """Extract text with strategy-based Tesseract configuration"""
        try:
            # Strategy-based configurations
            configs = {
                'standard': '--oem 3 --psm 3 -c preserve_interword_spaces=1 -c textord_force_make_proportional=1',
                'blurry': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c textord_min_linesize=3.0',
                'amharic': '--oem 1 --psm 6 -c preserve_interword_spaces=1 -c textord_old_baselines=1',
                'fallback': '--oem 3 --psm 4 -c preserve_interword_spaces=1'
            }
            
            config = configs.get(strategy, configs['standard'])
            
            # Special handling for Amharic
            if 'amh' in lang_code and strategy != 'amharic':
                config = configs['amharic']
            
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
    
    def _tesseract_extract_custom(self, image, lang_code, custom_config):
        """Custom Tesseract extraction with specific config"""
        try:
            text = pytesseract.image_to_string(
                image,
                lang=lang_code,
                config=custom_config,
                timeout=30
            )
            return self.enhanced_clean_text(text)
        except Exception as e:
            logger.error(f"Custom Tesseract error: {e}")
            return ""
    
def enhanced_preprocess_image(self, image_bytes):
    """Advanced image preprocessing for better OCR accuracy"""
    try:
        if OPENCV_AVAILABLE and cv2 and np:
            # Use OpenCV for better preprocessing
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Could not decode image with OpenCV")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Multiple preprocessing techniques
            processed = self.apply_advanced_preprocessing(gray)
            
            # Convert back to PIL Image for Tesseract
            pil_image = Image.fromarray(processed)
            return pil_image
        else:
            # Fallback to PIL processing
            return self.basic_pil_preprocessing(image_bytes)
            
    except Exception as e:
        logger.error("Enhanced preprocessing error: %s", e)
        # Fallback to basic PIL processing
        return self.basic_pil_preprocessing(image_bytes)
    def apply_advanced_preprocessing(self, gray_image):
        """Apply multiple preprocessing techniques"""
        # Technique 1: Denoising
        denoised = cv2.fastNlMeansDenoising(gray_image, None, h=20, templateWindowSize=7, searchWindowSize=21)
        
        # Technique 2: Contrast enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        contrast_enhanced = clahe.apply(denoised)
        
        # Technique 3: Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
        
        # Technique 4: Adaptive thresholding
        thresh = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Technique 5: Morphological operations to clean up
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def enhanced_deblur_processing(self, image_bytes):
        """Special processing for blurry images"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Stronger denoising for blurry images
            denoised = cv2.fastNlMeansDenoising(gray, None, h=40, templateWindowSize=9, searchWindowSize=21)
            
            # Stronger sharpening
            kernel = np.array([[-2,-2,-2], [-2,17,-2], [-2,-2,-2]]) / 9.0
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            # Bilateral filter for edge preservation
            bilateral = cv2.bilateralFilter(sharpened, 9, 75, 75)
            
            # High contrast adaptive threshold
            thresh = cv2.adaptiveThreshold(bilateral, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 15, 5)
            
            pil_image = Image.fromarray(thresh)
            return pil_image
            
        except Exception as e:
            logger.error("Deblur processing failed: %s", e)
            return self.basic_pil_preprocessing(image_bytes)
    
    def preprocess_for_amharic(self, image_bytes):
        """Special preprocessing for Amharic script"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Amharic benefits from different processing
            # Less aggressive denoising to preserve character details
            denoised = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=5, searchWindowSize=15)
            
            # Moderate contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            contrast_enhanced = clahe.apply(denoised)
            
            # Gentle sharpening
            kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
            sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
            
            # Otsu's thresholding for Amharic
            _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            pil_image = Image.fromarray(thresh)
            return pil_image
            
        except Exception as e:
            logger.error("Amharic preprocessing failed: %s", e)
            return self.basic_pil_preprocessing(image_bytes)
    
    def basic_pil_preprocessing(self, image_bytes):
        """Basic PIL-based preprocessing fallback"""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            return image
        except Exception as e:
            logger.error("Basic PIL preprocessing failed: %s", e)
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def enhanced_clean_text(self, text):
        """Advanced text cleaning preserving structure"""
        if not text:
            return ""
        
        lines = text.split('\n')
        filtered_lines = []
        prev_empty = False
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Clean the line but preserve original spacing
                cleaned_line = self.clean_text_line(line)
                filtered_lines.append(cleaned_line)
                prev_empty = False
            elif not prev_empty:
                filtered_lines.append('')
                prev_empty = True
        
        result = '\n'.join(filtered_lines).rstrip()
        
        if len(result.strip()) < 5:
            return "📝 Very little text detected. Please try:\n• Higher quality image\n• Better lighting conditions\n• Clearer text focus\n• Less complex background"
        
        return result
    
    def clean_text_line(self, line):
        """Clean individual text line while preserving structure"""
        # Remove common OCR artifacts but preserve meaningful characters
        line = line.replace('|', 'I').replace('0', 'O').replace('1', 'I')
        
        # Preserve Amharic and other special characters
        # Remove only obvious garbage characters
        import re
        line = re.sub(r'[^\w\s\u1200-\u137F\u2D80-\u2DDF\uAB00-\uAB2F.,!?;:()\[\]{}\-@#$%&*+=]', '', line)
        
        return line
    
    def fix_bullet_artifacts(self, text):
        """Fix common bullet artifacts"""
        lines = text.split('\n')
        fixed_lines = []
        bullet_chars = ['e', 'o', '0', 'point', '•', '*', '-', '–', '°', '·']
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                for bullet in bullet_chars:
                    if stripped.startswith(bullet + ' ') or stripped == bullet:
                        line = line.replace(bullet, '•', 1)
                        break
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

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