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
    validate_ocr_result, clean_ocr_text, get_fallback_strategy,
    get_script_family, get_language_from_script, LANGUAGE_MAPPING
)

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Setup Tesseract and verify installation"""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract v{version} initialized")
            
            # Try to get available languages (this might not work in all environments)
            try:
                # This is a best-effort attempt to list languages
                from subprocess import check_output
                langs = check_output(['tesseract', '--list-langs'], text=True).strip().split('\n')[1:]
                logger.info(f"📚 Available languages: {len(langs)} languages")
            except:
                logger.info("📚 Language detection not available - using universal mode")
                
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            return False
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Universal text extraction for all languages"""
        start_time = time.time()
        
        try:
            # Stage 1: Smart preprocessing
            processed_image, image_size = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.universal_preprocessing,
                image_bytes
            )
            
            # Stage 2: Advanced language detection
            detected_language = await self.advanced_language_detection(processed_image)
            logger.info(f"🔍 Detected language: {detected_language} ({LANGUAGE_MAPPING.get(detected_language, 'Unknown')})")
            
            # Stage 3: Multi-stage OCR with fallbacks
            text = await self.universal_ocr_processing(
                processed_image, 
                detected_language, 
                image_size
            )
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 5:
                return "🔍 No readable text found. Please try a clearer image with better contrast."
            
            # Stage 4: Intelligent text cleaning
            cleaned_text = clean_ocr_text(text, detected_language)
            
            logger.info(f"✅ {LANGUAGE_MAPPING.get(detected_language, 'Unknown')} OCR completed in {processing_time:.2f}s")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return "❌ Processing error: Please try a different image or check image quality."
    
    async def advanced_language_detection(self, processed_image):
        """Advanced language detection using multiple strategies"""
        loop = asyncio.get_event_loop()
        
        try:
            # Strategy 1: OSD-based detection
            osd_result = await loop.run_in_executor(
                thread_pool,
                self._get_osd_data,
                processed_image
            )
            
            script = self._extract_script_from_osd(osd_result)
            logger.info(f"📜 OSD detected script: {script}")
            
            # Strategy 2: Quick multi-language sampling
            candidate_language = await self.quick_language_sampling(processed_image, script)
            
            # Strategy 3: Text-based validation
            if candidate_language:
                # Verify with a quick OCR
                test_text = await self.quick_ocr_test(processed_image, candidate_language)
                if test_text and self.validate_language_choice(test_text, candidate_language):
                    return candidate_language
            
            # Final fallback based on script
            final_lang = get_language_from_script(script)
            logger.info(f"🎯 Final language selection: {final_lang}")
            return final_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}, defaulting to English")
            return 'en'
    
    async def quick_language_sampling(self, processed_image, script):
        """Quick sampling of likely languages for the detected script"""
        loop = asyncio.get_event_loop()
        
        # Map scripts to candidate languages
        script_candidates = {
            'Latin': ['en', 'es', 'fr', 'de', 'it', 'pt'],
            'Cyrillic': ['ru', 'uk', 'bg'],
            'Arabic': ['ar', 'fa', 'ur'],
            'Chinese': ['zh'],
            'Japanese': ['ja'],
            'Korean': ['ko'],
            'Ethiopic': ['am'],
            'Devanagari': ['hi', 'ne'],
            'Bengali': ['bn'],
            'Thai': ['th'],
            'Hebrew': ['he'],
            'Greek': ['el']
        }
        
        candidates = script_candidates.get(script, ['en'])
        best_lang = 'en'
        best_score = 0
        
        for lang_code in candidates:
            try:
                tesseract_lang = get_tesseract_code(lang_code)
                config = get_ocr_config(lang_code, script, (100, 100))
                
                test_text = await self.extract_with_tesseract(
                    processed_image, tesseract_lang, config, quick=True
                )
                
                if test_text and len(test_text.strip()) > 5:
                    score = self.calculate_language_score(test_text, lang_code)
                    if score > best_score:
                        best_score = score
                        best_lang = lang_code
                        
            except Exception as e:
                continue
        
        return best_lang if best_score > 10 else 'en'
    
    def calculate_language_score(self, text, language):
        """Calculate confidence score for language detection"""
        if not text:
            return 0
        
        script_family = get_script_family(language)
        expected_script = detect_script_from_text(text)
        
        # Bonus if scripts match
        script_bonus = 10 if script_family == expected_script else 0
        
        # Base score from text length and validation
        is_valid, message = validate_ocr_result(text, language)
        validation_bonus = 15 if is_valid else 0
        
        return len(text.strip()) + script_bonus + validation_bonus
    
    async def quick_ocr_test(self, processed_image, language):
        """Quick OCR test for language validation"""
        try:
            tesseract_lang = get_tesseract_code(language)
            config = get_ocr_config(language, get_script_family(language), (100, 100))
            
            text = await self.extract_with_tesseract(
                processed_image, tesseract_lang, config, quick=True
            )
            return text
        except:
            return None
    
    def validate_language_choice(self, text, language):
        """Validate if the detected language makes sense for the text"""
        if not text or len(text.strip()) < 5:
            return False
        
        detected_script = detect_script_from_text(text)
        expected_script = get_script_family(language)
        
        # Allow some flexibility in script matching
        script_compatibility = {
            'Latin': ['Latin'],
            'Cyrillic': ['Cyrillic'],
            'Arabic': ['Arabic'],
            'Chinese': ['Chinese', 'Japanese'],  # Chinese characters in Japanese
            'Japanese': ['Japanese', 'Chinese'],  # Kanji in Japanese
            'Korean': ['Korean'],
            'Ethiopic': ['Ethiopic'],
            'Devanagari': ['Devanagari'],
            'Bengali': ['Bengali'],
            'Thai': ['Thai'],
            'Hebrew': ['Hebrew'],
            'Greek': ['Greek']
        }
        
        compatible_scripts = script_compatibility.get(expected_script, [expected_script])
        return detected_script in compatible_scripts
    
    async def universal_ocr_processing(self, processed_image, language, image_size):
        """Universal OCR processing with intelligent fallbacks"""
        primary_tesseract_lang = get_tesseract_code(language)
        script_family = get_script_family(language)
        
        # Primary strategy
        strategies = [
            (primary_tesseract_lang, get_ocr_config(language, script_family, image_size)),
        ]
        
        # Add script-specific fallbacks
        fallback_langs = get_fallback_strategy(language)
        for fallback in fallback_langs:
            if fallback != primary_tesseract_lang:
                fallback_script = get_script_family(language)  # Use same script family
                strategies.append(
                    (fallback, get_ocr_config(language, fallback_script, image_size))
                )
        
        # Add universal fallbacks
        strategies.extend([
            (primary_tesseract_lang, "--oem 3 --psm 3"),  # Fully automatic
            ("eng", "--oem 3 --psm 6"),  # English fallback
            ("osd", "--oem 3 --psm 3"),  # OSD fallback
        ])
        
        best_text = ""
        best_score = 0
        
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text:
                    score = self.evaluate_text_quality(text, language)
                    
                    if score > best_score:
                        best_score = score
                        best_text = text
                        
                    # Early exit for high-quality results
                    if score > 50 and len(text.strip()) > 20:
                        break
                        
            except Exception as e:
                logger.debug(f"OCR strategy failed: {lang} {config}")
                continue
        
        return best_text
    
    def evaluate_text_quality(self, text, language):
        """Evaluate text quality with comprehensive scoring"""
        if not text:
            return 0
        
        base_score = len(text.strip())
        
        # Validation bonus
        is_valid, message = validate_ocr_result(text, language)
        if is_valid:
            base_score += 20
        
        # Script consistency bonus
        detected_script = detect_script_from_text(text)
        expected_script = get_script_family(language)
        if detected_script == expected_script:
            base_score += 15
        
        # Character diversity bonus
        unique_chars = len(set(text))
        if unique_chars > 10:
            base_score += 10
        
        return base_score
    
    def universal_preprocessing(self, image_bytes):
        """Universal preprocessing that works for all scripts"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Universal contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.4)
            
            # Universal brightness adjustment
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # Mild sharpening for all images
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Resize very small images
            if min(image.size) < 400:
                scale_factor = 800 / min(image.size)
                new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image, original_size
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return image, image.size
    
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
                script_map = {
                    'Latin': 'Latin',
                    'Cyrillic': 'Cyrillic',
                    'Arabic': 'Arabic',
                    'HanS': 'Chinese',
                    'Hangul': 'Korean',
                    'Japanese': 'Japanese',
                    'Ethiopic': 'Ethiopic',
                    'Thai': 'Thai',
                    'Devanagari': 'Devanagari',
                    'Bengali': 'Bengali',
                    'Hebrew': 'Hebrew',
                    'Greek': 'Greek'
                }
                return script_map.get(script, 'Latin')
        return "Latin"
    
    async def extract_with_tesseract(self, image, lang, config, quick=False):
        """Extract text with Tesseract with optimized timeout"""
        loop = asyncio.get_event_loop()
        timeout = 10.0 if quick else 25.0
        
        try:
            text = await asyncio.wait_for(
                loop.run_in_executor(
                    thread_pool,
                    self._tesseract_extract,
                    image,
                    lang,
                    config
                ),
                timeout=timeout
            )
            return text
        except asyncio.TimeoutError:
            logger.warning(f"Tesseract timeout for {lang}")
            return ""
        except Exception as e:
            logger.debug(f"Tesseract extraction failed for {lang}: {e}")
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
            logger.debug(f"Tesseract error for {lang}: {e}")
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
        return f"Average: {avg_time:.2f}s"

performance_monitor = PerformanceMonitor()