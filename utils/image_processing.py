# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import pytesseract
from concurrent.futures import ThreadPoolExecutor
from ocr_engine.language_support import (
    get_tesseract_code, get_ocr_config, detect_script_from_text,
    validate_ocr_result, clean_ocr_text, get_fallback_languages,
    get_script_family, CORE_LANGUAGES
)

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Setup Tesseract"""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized")
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            return False
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Optimized text extraction with multi-stage processing"""
        start_time = time.time()
        
        try:
            # Stage 1: Enhanced preprocessing
            processed_image, image_size = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.adaptive_preprocessing,
                image_bytes
            )
            
            # Stage 2: Fast language detection
            detected_language = await self.fast_language_detection(processed_image)
            logger.info(f"🔍 Detected language: {detected_language}")
            
            # Stage 3: Multi-strategy OCR
            text = await self.multi_strategy_ocr(
                processed_image, 
                detected_language, 
                image_size
            )
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 5:
                return "🔍 No readable text found. Please try a clearer image."
            
            # Stage 4: Smart text cleaning
            cleaned_text = clean_ocr_text(text, detected_language)
            
            logger.info(f"✅ {detected_language.upper()} OCR completed in {processing_time:.2f}s")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return f"❌ Processing error: Please try a different image."
    
    async def fast_language_detection(self, processed_image):
        """Fast and accurate language detection"""
        loop = asyncio.get_event_loop()
        
        try:
            # Try OSD first for script detection
            osd_result = await loop.run_in_executor(
                thread_pool,
                self._get_osd_data,
                processed_image
            )
            
            script = self._extract_script_from_osd(osd_result)
            logger.info(f"📜 OSD detected script: {script}")
            
            # Quick test with core languages from the detected script family
            test_languages = self._get_test_languages_for_script(script)
            best_lang = 'en'
            best_score = 0
            
            for lang_code in test_languages[:3]:  # Test top 3
                try:
                    tesseract_lang = get_tesseract_code(lang_code)
                    config = get_ocr_config(lang_code, script, (100, 100))
                    
                    test_text = await self.extract_with_tesseract(
                        processed_image, tesseract_lang, config
                    )
                    
                    if test_text and len(test_text.strip()) > 10:
                        # Score based on text length and validation
                        is_valid, message = validate_ocr_result(test_text, lang_code)
                        score = len(test_text.strip()) * (2 if is_valid else 1)
                        
                        if score > best_score:
                            best_score = score
                            best_lang = lang_code
                            
                except Exception as e:
                    continue
            
            return best_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    def _get_test_languages_for_script(self, script):
        """Get test languages for script detection"""
        script_languages = {
            'Latin': ['en', 'es', 'fr', 'de'],
            'Cyrillic': ['ru', 'uk', 'bg'],
            'Arabic': ['ar', 'fa', 'ur'],
            'Chinese': ['zh'],
            'Japanese': ['ja'],
            'Korean': ['ko'],
            'Ethiopic': ['am', 'ti'],
            'Devanagari': ['hi', 'ne'],
            'Thai': ['th']
        }
        return script_languages.get(script, ['en', 'es', 'fr'])
    
    async def multi_strategy_ocr(self, processed_image, language, image_size):
        """Multi-strategy OCR with fallbacks"""
        tesseract_lang = get_tesseract_code(language)
        script_family = get_script_family(language)
        
        strategies = [
            # Primary strategy
            (tesseract_lang, get_ocr_config(language, script_family, image_size)),
            # Fallback strategy
            (tesseract_lang, get_ocr_config(language, script_family, None)),
            # Auto PSM
            (tesseract_lang, "--oem 3 --psm 3"),
        ]
        
        # Add English fallback for non-English languages
        if language != 'en':
            strategies.append(("eng", get_ocr_config('en', 'Latin', image_size)))
        
        best_text = ""
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and self._is_better_text(text, best_text, language):
                    best_text = text
                    
                    # Early exit if we get good quality text
                    is_valid, message = validate_ocr_result(text, language)
                    if is_valid and len(text.strip()) > 20:
                        break
                        
            except Exception as e:
                logger.debug(f"OCR strategy failed: {lang} {config}: {e}")
                continue
        
        return best_text
    
    def _is_better_text(self, new_text, current_text, language):
        """Determine if new text is better than current"""
        if not current_text:
            return True
        
        new_len = len(new_text.strip())
        current_len = len(current_text.strip())
        
        # Prefer longer valid text
        is_valid, message = validate_ocr_result(new_text, language)
        current_valid, _ = validate_ocr_result(current_text, language)
        
        if is_valid and not current_valid:
            return True
        elif is_valid and current_valid and new_len > current_len:
            return True
        
        return False
    
    def adaptive_preprocessing(self, image_bytes):
        """Adaptive preprocessing based on image characteristics"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Calculate image statistics for adaptive processing
            brightness = self._calculate_brightness(image)
            contrast = self._estimate_contrast(image)
            
            # Adaptive contrast enhancement
            if contrast < 0.3:  # Low contrast
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
            elif contrast > 0.7:  # High contrast
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(0.8)
            else:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.3)
            
            # Adaptive brightness
            if brightness < 0.3:  # Dark image
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(1.4)
            elif brightness > 0.7:  # Bright image
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(0.8)
            
            # Mild sharpening for all images
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Resize if image is very small
            if min(image.size) < 300:
                scale_factor = 600 / min(image.size)
                new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image, original_size
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return image, image.size
    
    def _calculate_brightness(self, image):
        """Calculate image brightness"""
        hist = image.histogram()
        pixels = sum(hist)
        brightness = scale = len(hist)
        
        for index in range(scale):
            ratio = hist[index] / pixels
            brightness += ratio * (-scale + index)
        
        return brightness / scale
    
    def _estimate_contrast(self, image):
        """Estimate image contrast"""
        import numpy as np
        arr = np.array(image)
        return float(arr.std()) / 255
    
    def _get_osd_data(self, image):
        """Get OSD data from image"""
        try:
            return pytesseract.image_to_osd(image, config='--psm 0')
        except:
            return ""
    
    def _extract_script_from_osd(self, osd_result):
        """Extract script from OSD result"""
        if not osd_result:
            return "Latin"
        
        for line in osd_result.split('\n'):
            if line.startswith('Script:'):
                script = line.split(':')[1].strip()
                # Map OSD script names to our script families
                script_map = {
                    'Latin': 'Latin',
                    'Cyrillic': 'Cyrillic',
                    'Arabic': 'Arabic',
                    'HanS': 'Chinese',
                    'Hangul': 'Korean',
                    'Japanese': 'Japanese',
                    'Ethiopic': 'Ethiopic',
                    'Thai': 'Thai',
                    'Devanagari': 'Devanagari'
                }
                return script_map.get(script, 'Latin')
        return "Latin"
    
    async def extract_with_tesseract(self, image, lang, config):
        """Extract text with Tesseract with timeout"""
        loop = asyncio.get_event_loop()
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(
                    thread_pool,
                    self._tesseract_extract,
                    image,
                    lang,
                    config
                ),
                timeout=20.0
            )
            return text
        except asyncio.TimeoutError:
            logger.warning(f"Tesseract timeout for {lang}")
            return ""
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
                timeout=15
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
        if len(self.request_times) > 50:
            self.request_times.pop(0)
    
    def get_stats(self):
        if not self.request_times:
            return "No requests yet"
        avg_time = sum(self.request_times) / len(self.request_times)
        return f"Average: {avg_time:.2f}s, Last 10: {sum(self.request_times[-10:])/min(10, len(self.request_times)):.2f}s"

performance_monitor = PerformanceMonitor()