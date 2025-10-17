# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import get_tesseract_code, get_language_family, is_complex_script

# Try to import OpenCV headless
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ OpenCV headless loaded successfully")
except ImportError as e:
    OPENCV_AVAILABLE = False
    logger.warning(f"⚠️ OpenCV headless not available: {e}. Using PIL fallback.")

logger = logging.getLogger(__name__)

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
        """Enhanced text extraction optimized for Amharic and blurry images"""
        start_time = time.time()
        
        try:
            # Detect script first to determine optimal processing
            initial_image = Image.open(io.BytesIO(image_bytes)).convert('L')
            script = await self.detect_script(initial_image)
            logger.info(f"📝 Detected script: {script}")
            
            # Apply script-specific preprocessing
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.script_specific_preprocessing,
                image_bytes,
                script
            )
            
            # Determine language based on script
            lang_code = self.get_lang_from_script(script)
            
            # Enhanced Amharic detection
            if script == 'Ethiopic' or 'amh' in str(script).lower() or lang_code == 'am':
                lang_code = 'am'
                logger.info("🔤 Using enhanced Amharic processing")
                
                # Try multiple Amharic-specific strategies
                text = await self.amharic_specific_ocr(processed_image, image_bytes)
            else:
                # Standard multi-strategy OCR for other languages
                available_langs = self.get_tesseract_languages()
                text = await self.multi_strategy_ocr(processed_image, lang_code, available_langs, image_bytes, script)
            
            processing_time = time.time() - start_time
            logger.info(f"⚡ OCR completed in {processing_time:.2f}s")
            
            if not text or len(text.strip()) < 3:
                return "🔍 No readable text found. Please try a clearer image with better lighting and contrast."
            
            return text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return f"❌ OCR processing error. Please try a different image or check image quality."
    
    async def amharic_specific_ocr(self, processed_image, original_image_bytes):
        """Specialized OCR processing for Amharic text"""
        strategies = []
        
        # Strategy 1: Gentle preprocessing with Amharic config
        gentle_image = await asyncio.get_event_loop().run_in_executor(
            thread_pool,
            self.gentle_amharic_preprocessing,
            original_image_bytes
        )
        strategies.append(('gentle_amharic', gentle_image, '--oem 1 --psm 6'))
        
        # Strategy 2: Medium preprocessing
        medium_image = await asyncio.get_event_loop().run_in_executor(
            thread_pool,
            self.medium_amharic_preprocessing,
            original_image_bytes
        )
        strategies.append(('medium_amharic', medium_image, '--oem 1 --psm 4'))
        
        # Strategy 3: Original processed image
        strategies.append(('standard_amharic', processed_image, '--oem 1 --psm 3'))
        
        # Strategy 4: For blurry Amharic images
        blurry_image = await asyncio.get_event_loop().run_in_executor(
            thread_pool,
            self.blurry_amharic_preprocessing,
            original_image_bytes
        )
        strategies.append(('blurry_amharic', blurry_image, '--oem 1 --psm 6 -c textord_min_linesize=2.5'))
        
        best_result = ""
        best_confidence = 0
        
        for strategy_name, strategy_image, config in strategies:
            try:
                text = await self.extract_with_tesseract_custom(strategy_image, 'amh+amh_vert+eng', config)
                confidence = self.calculate_amharic_confidence(text)
                
                logger.info(f"🔤 Amharic strategy '{strategy_name}': confidence {confidence:.1f}%")
                
                if confidence > best_confidence:
                    best_result = text
                    best_confidence = confidence
                    
                    # Early exit if we get very good confidence
                    if confidence > 80:
                        break
            except Exception as e:
                logger.warning(f"Amharic strategy {strategy_name} failed: {e}")
                continue
        
        if best_result and best_confidence > 30:
            return self.clean_amharic_text(best_result)
        else:
            # Fallback to English if Amharic fails completely
            logger.warning("Amharic OCR failed, falling back to English")
            fallback_text = await self.extract_with_tesseract_enhanced(processed_image, 'eng', 'fallback')
            return f"⚠️ Amharic text not clearly recognized. English fallback:\n\n{fallback_text}"
    
    def calculate_amharic_confidence(self, text):
        """Calculate confidence specifically for Amharic text"""
        if not text or len(text.strip()) < 3:
            return 0
        
        # Count Amharic Unicode characters (Ethiopic block: U+1200 to U+137F)
        amharic_chars = sum(1 for c in text if '\u1200' <= c <= '\u137f')
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return 0
        
        # Base confidence on percentage of Amharic characters
        amharic_ratio = (amharic_chars / total_chars) * 100
        
        # Also consider overall text quality
        readable_chars = sum(1 for c in text if c.isalnum() or c.isspace() or '\u1200' <= c <= '\u137f')
        quality_ratio = (readable_chars / total_chars) * 100
        
        final_confidence = (amharic_ratio * 0.7) + (quality_ratio * 0.3)
        return min(final_confidence, 100)
    
    def clean_amharic_text(self, text):
        """Clean and validate Amharic text"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Remove lines that are mostly non-Amharic
                amharic_chars = sum(1 for c in line if '\u1200' <= c <= '\u137f')
                if amharic_chars >= 1 or len(line) > 10:  # Keep lines with Amharic chars or reasonable length
                    cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        if not result.strip():
            return "🔍 Amharic text not clearly recognized. Please ensure:\n• Clear, high-contrast image\n• Proper lighting\n• Horizontal text alignment\n• Minimal background noise"
        
        return result
    
    async def multi_strategy_ocr(self, processed_image, lang_code, available_langs, original_image_bytes, script):
        """Multi-strategy OCR for non-Amharic languages"""
        strategies = [
            ('standard', processed_image, '--oem 3 --psm 3'),
            ('single_block', processed_image, '--oem 3 --psm 6'),
            ('single_line', processed_image, '--oem 3 --psm 7'),
            ('blurry_fallback', processed_image, '--oem 3 --psm 4')
        ]
        
        best_result = ""
        best_confidence = 0
        
        for strategy_name, strategy_image, config in strategies:
            try:
                tesseract_lang = get_tesseract_code(lang_code)
                if tesseract_lang not in available_langs:
                    tesseract_lang = 'eng'
                
                text = await self.extract_with_tesseract_custom(strategy_image, tesseract_lang, config)
                confidence = self.estimate_confidence(text)
                
                if confidence > best_confidence:
                    best_result = text
                    best_confidence = confidence
                    
                    if confidence > 75:
                        break
            except Exception as e:
                continue
        
        return best_result if best_result else "No readable text found."
    
    def script_specific_preprocessing(self, image_bytes, script):
        """Apply preprocessing optimized for specific script types"""
        try:
            if script == 'Ethiopic' or script == 'Amharic':
                # Gentle preprocessing for Amharic - preserve character details
                return self.gentle_amharic_preprocessing(image_bytes)
            elif script in ['Arabic', 'Hebrew']:
                # Right-to-left scripts need special handling
                return self.rtl_script_preprocessing(image_bytes)
            else:
                # Standard preprocessing for Latin, Cyrillic, etc.
                return self.standard_preprocessing(image_bytes)
        except Exception as e:
            logger.error(f"Script-specific preprocessing failed: {e}")
            return self.standard_preprocessing(image_bytes)
    
    def gentle_amharic_preprocessing(self, image_bytes):
        """Gentle preprocessing optimized for Amharic characters"""
        try:
            if OPENCV_AVAILABLE:
                # Use OpenCV for Amharic-specific preprocessing
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    return self.pil_amharic_preprocessing(image_bytes)
                
                # Convert to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Gentle denoising for Amharic (preserve character details)
                denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
                
                # Mild contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(denoised)
                
                # Very mild sharpening
                kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
                sharpened = cv2.filter2D(enhanced, -1, kernel)
                
                # Adaptive threshold for Amharic
                binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY, 11, 2)
                
                pil_image = Image.fromarray(binary)
                return pil_image
            else:
                return self.pil_amharic_preprocessing(image_bytes)
                
        except Exception as e:
            logger.error(f"Gentle Amharic preprocessing failed: {e}")
            return self.pil_amharic_preprocessing(image_bytes)
    
    def pil_amharic_preprocessing(self, image_bytes):
        """PIL-based preprocessing for Amharic"""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            
            # Mild contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Mild sharpness enhancement
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            # Gentle noise reduction
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
        except Exception as e:
            logger.error(f"PIL Amharic preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def medium_amharic_preprocessing(self, image_bytes):
        """Medium preprocessing for challenging Amharic images"""
        try:
            if OPENCV_AVAILABLE:
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    return self.pil_amharic_preprocessing(image_bytes)
                
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Medium denoising
                denoised = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)
                
                # Medium contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                enhanced = clahe.apply(denoised)
                
                # Medium sharpening
                kernel = np.array([[-0.5, -0.5, -0.5], [-0.5, 5, -0.5], [-0.5, -0.5, -0.5]])
                sharpened = cv2.filter2D(enhanced, -1, kernel)
                
                # Otsu's thresholding
                _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                pil_image = Image.fromarray(binary)
                return pil_image
            else:
                return self.pil_amharic_preprocessing(image_bytes)
        except Exception as e:
            logger.error(f"Medium Amharic preprocessing failed: {e}")
            return self.pil_amharic_preprocessing(image_bytes)
    
    def blurry_amharic_preprocessing(self, image_bytes):
        """Special preprocessing for blurry Amharic images"""
        try:
            if OPENCV_AVAILABLE:
                nparr = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    return self.pil_amharic_preprocessing(image_bytes)
                
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Stronger denoising for blurry images
                denoised = cv2.fastNlMeansDenoising(gray, None, h=20, templateWindowSize=9, searchWindowSize=21)
                
                # Strong contrast enhancement for blurry text
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
                enhanced = clahe.apply(denoised)
                
                # Strong sharpening for blurry images
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                sharpened = cv2.filter2D(enhanced, -1, kernel)
                
                # Morphological operations to connect broken characters
                kernel = np.ones((2,2), np.uint8)
                closed = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, kernel)
                
                # Adaptive threshold for blurry text
                binary = cv2.adaptiveThreshold(closed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY, 15, 5)
                
                pil_image = Image.fromarray(binary)
                return pil_image
            else:
                image = Image.open(io.BytesIO(image_bytes)).convert('L')
                # Enhanced preprocessing for blurry images using PIL
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.5)
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(3.0)
                image = image.filter(ImageFilter.SHARPEN)
                return image
        except Exception as e:
            logger.error(f"Blurry Amharic preprocessing failed: {e}")
            return self.pil_amharic_preprocessing(image_bytes)
    
    def standard_preprocessing(self, image_bytes):
        """Standard preprocessing for non-Amharic scripts"""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            return image
        except Exception as e:
            logger.error(f"Standard preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def rtl_script_preprocessing(self, image_bytes):
        """Preprocessing for right-to-left scripts"""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.8)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            return image
        except Exception as e:
            logger.error(f"RTL preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    def estimate_confidence(self, text):
        """Estimate confidence based on text quality"""
        if not text or len(text.strip()) < 3:
            return 0
        
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
                image,
                '--psm 0'
            )
            for line in osd.split('\n'):
                if line.startswith('Script:'):
                    script = line.split(':')[1].strip()
                    logger.info(f"📜 OSD detected script: {script}")
                    return script
            return 'Latin'
        except Exception as e:
            logger.warning(f"Script detection failed: {e}, defaulting to Latin")
            return 'Latin'
    
    def get_lang_from_script(self, script):
        """Map script to language code"""
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
        return mapping.get(script, 'eng')
    
    async def extract_with_tesseract_enhanced(self, image, lang_code, strategy='standard'):
        """Enhanced Tesseract extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_enhanced,
            image,
            lang_code,
            strategy
        )
    
    async def extract_with_tesseract_custom(self, image, lang_code, custom_config):
        """Custom Tesseract extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_custom,
            image,
            lang_code,
            custom_config
        )
    
    def _tesseract_extract_enhanced(self, image, lang_code, strategy):
        """Extract text with Tesseract"""
        try:
            configs = {
                'standard': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
                'fallback': '--oem 3 --psm 6 -c preserve_interword_spaces=1'
            }
            
            config = configs.get(strategy, configs['standard'])
            
            text = pytesseract.image_to_string(
                image,
                lang=lang_code,
                config=config,
                timeout=30
            )
            
            return text.strip() if text else ""
            
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return ""
    
    def _tesseract_extract_custom(self, image, lang_code, custom_config):
        """Custom Tesseract extraction"""
        try:
            text = pytesseract.image_to_string(
                image,
                lang=lang_code,
                config=custom_config,
                timeout=30
            )
            return text.strip() if text else ""
        except Exception as e:
            logger.error(f"Custom Tesseract error: {e}")
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