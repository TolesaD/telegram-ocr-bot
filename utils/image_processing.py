# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ocr_")

# Import your comprehensive language support - MOVED AFTER logger DEFINITION
try:
    from ocr_engine.language_support import (
        TESSERACT_LANGUAGES, SCRIPT_FAMILIES, get_script_family,
        get_tesseract_code, get_ocr_config, detect_script_from_text,
        get_fallback_strategy, clean_ocr_text, validate_ocr_result,
        detect_primary_language, get_language_confidence,
        get_supported_languages, get_language_name
    )
    LANGUAGE_SUPPORT_AVAILABLE = True
    logger.info("✅ Comprehensive language support loaded")
except ImportError as e:
    LANGUAGE_SUPPORT_AVAILABLE = False
    logger.warning(f"❌ Language support module not available: {e}")
    LANGUAGE_SUPPORT_AVAILABLE = False

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
        self.available_languages = []
        self._load_available_languages()
    
    def setup_tesseract(self):
        """Setup Tesseract with automatic path detection"""
        try:
            # Try to find Tesseract automatically
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
        """Find Tesseract installation path with better detection"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract', 
            '/bin/tesseract',
            '/app/bin/tesseract',
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
        ]
        
        # First try system PATH
        try:
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                logger.info(f"🔍 Found Tesseract via PATH: {tesseract_path}")
                return tesseract_path
        except:
            pass
        
        # Check possible paths
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"🔍 Found Tesseract at: {path}")
                return path
        
        logger.error("❌ Could not find Tesseract in any known location")
        return None

    def _load_available_languages(self):
        """Load available Tesseract languages"""
        try:
            # Get languages using pytesseract
            langs_output = subprocess.run([
                pytesseract.pytesseract.tesseract_cmd, '--list-langs'
            ], capture_output=True, text=True, timeout=10)
            
            if langs_output.returncode == 0:
                # Parse the output to get language list
                lines = langs_output.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Skip the first line ("List of available languages:")
                    self.available_languages = lines[1:]
                else:
                    self.available_languages = ['eng']  # Default fallback
            else:
                self.available_languages = ['eng']  # Default fallback
                
            logger.info(f"📚 Found {len(self.available_languages)} available languages: {self.available_languages}")
            
        except Exception as e:
            logger.error(f"Error loading available languages: {e}")
            self.available_languages = ['eng']

    def get_optimized_language_config(self, processed_image=None):
        """Get optimized language configuration using language support module"""
        if not LANGUAGE_SUPPORT_AVAILABLE:
            return self.get_multilingual_config()
        
        # If we have an image, try to detect script from a quick OCR
        detected_script = 'Latin'  # Default
        if processed_image:
            try:
                # Quick OCR to detect script
                quick_text = pytesseract.image_to_string(
                    processed_image, 
                    lang='osd',  # Orientation and script detection
                    config='--psm 0 --oem 3'
                )
                if quick_text:
                    detected_script = detect_script_from_text(quick_text)
                    logger.info(f"🔍 Detected script: {detected_script}")
            except Exception as e:
                logger.warning(f"Script detection failed: {e}")
        
        # Get languages for the detected script
        script_languages = SCRIPT_FAMILIES.get(detected_script, ['en'])
        
        # Convert to Tesseract codes and filter available ones
        tesseract_langs = []
        for lang_code in script_languages:
            tesseract_code = get_tesseract_code(lang_code)
            if tesseract_code in self.available_languages and tesseract_code not in tesseract_langs:
                tesseract_langs.append(tesseract_code)
        
        # If no languages found for script, use available languages
        if not tesseract_langs:
            tesseract_langs = self.available_languages[:3]  # Use first 3 available
        
        lang_config = '+'.join(tesseract_langs)
        logger.info(f"🌍 Using optimized language config: {lang_config} for {detected_script} script")
        return lang_config

    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with comprehensive multilingual support"""
        start_time = time.time()
        
        try:
            # Gentle preprocessing
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.preservative_preprocessing,
                image_bytes
            )
            
            # Try multiple OCR strategies with language detection
            text = await self.smart_multilingual_ocr(processed_image)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                logger.warning("❌ No text extracted or text too short")
                return "🔍 No readable text found. Please try a clearer image."
            
            # Clean text based on detected language
            if LANGUAGE_SUPPORT_AVAILABLE:
                detected_lang = detect_primary_language(text)
                cleaned_text = clean_ocr_text(text, detected_lang)
                
                # Validate the result
                is_valid, validation_msg = validate_ocr_result(cleaned_text, detected_lang)
                if not is_valid:
                    logger.warning(f"OCR validation failed: {validation_msg}")
            else:
                cleaned_text = self._minimal_clean_text(text)
            
            logger.info(f"✅ OCR completed in {processing_time:.2f}s")
            logger.info(f"📝 Extracted {len(cleaned_text)} characters")
            
            if LANGUAGE_SUPPORT_AVAILABLE:
                detected_lang = detect_primary_language(cleaned_text)
                lang_name = get_language_name(detected_lang)
                logger.info(f"🌍 Detected language: {lang_name} ({detected_lang})")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            logger.error(f"Full error details:", exc_info=True)
            return "❌ Error processing image. Please try again with a different image."

    async def smart_multilingual_ocr(self, processed_image):
        """Smart OCR with language detection and fallback strategies"""
        strategies = []
        
        if LANGUAGE_SUPPORT_AVAILABLE:
            # Strategy 1: Script-based optimized configuration
            optimized_lang = self.get_optimized_language_config(processed_image)
            strategies.append((optimized_lang, '--oem 3 --psm 6 -c preserve_interword_spaces=1'))
            
            # Strategy 2: Auto script detection
            strategies.append(('osd', '--oem 3 --psm 0'))  # Orientation and script detection
            
            # Strategy 3: Multiple scripts combined
            multi_script_langs = self.get_multi_script_config()
            strategies.append((multi_script_langs, '--oem 3 --psm 6'))
        else:
            # Fallback strategies without language support
            strategies.extend([
                (self.get_multilingual_config(), '--oem 3 --psm 6 -c preserve_interword_spaces=1'),
                ('eng+amh', '--oem 3 --psm 6'),
                ('eng', '--oem 3 --psm 6'),
            ])
        
        # Add universal fallback strategies
        strategies.extend([
            ('eng', '--oem 3 --psm 4'),
            ('eng', '--oem 3 --psm 8'),
        ])
        
        best_text = ""
        best_confidence = 0
        
        for i, (lang, config) in enumerate(strategies):
            try:
                logger.info(f"🔧 Trying OCR strategy {i+1}: {lang} with {config}")
                text = await self.extract_with_tesseract(processed_image, lang, config)
                
                if text and text.strip():
                    # Calculate confidence
                    confidence = self.calculate_text_confidence(text, lang)
                    
                    if confidence > best_confidence:
                        best_text = text
                        best_confidence = confidence
                        logger.info(f"✅ Strategy {i+1} confidence: {confidence:.2f}")
                    
                    # Early exit for high confidence results
                    if confidence > 0.7:
                        logger.info(f"🎯 High confidence result with strategy {i+1}")
                        break
                        
            except Exception as e:
                logger.warning(f"❌ Strategy {i+1} failed: {e}")
                continue
        
        return best_text

    def get_multi_script_config(self):
        """Get configuration for multiple scripts"""
        # Group available languages by script family
        script_groups = {}
        for lang_code in self.available_languages:
            # Find which script this language belongs to
            for script, languages in SCRIPT_FAMILIES.items():
                for lang in languages:
                    tesseract_code = get_tesseract_code(lang)
                    if tesseract_code == lang_code:
                        if script not in script_groups:
                            script_groups[script] = []
                        script_groups[script].append(lang_code)
                        break
        
        # Take up to 2 languages from each script group
        selected_langs = []
        for script, langs in script_groups.items():
            selected_langs.extend(langs[:2])
        
        # Limit to 6 languages total for performance
        selected_langs = selected_langs[:6]
        
        if not selected_langs:
            selected_langs = ['eng']  # Fallback
        
        return '+'.join(selected_langs)

    def calculate_text_confidence(self, text, lang_used):
        """Calculate confidence score for OCR result"""
        if not text:
            return 0
        
        text_length = len(text.strip())
        
        # Base confidence on text length
        length_confidence = min(text_length / 100.0, 1.0)
        
        # Character diversity
        unique_chars = len(set(text))
        diversity_confidence = min(unique_chars / 20.0, 1.0)
        
        # Language-specific confidence if available
        if LANGUAGE_SUPPORT_AVAILABLE:
            detected_lang = detect_primary_language(text)
            lang_confidence = get_language_confidence(text, detected_lang)
        else:
            lang_confidence = 0.5
        
        # Combined confidence
        total_confidence = (length_confidence * 0.4 + 
                          diversity_confidence * 0.3 + 
                          lang_confidence * 0.3)
        
        return total_confidence

    def get_multilingual_config(self):
        """Get optimal language configuration based on available languages"""
        # Priority languages to try
        priority_languages = ['eng', 'amh', 'ara', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'chi_sim', 'jpn', 'kor']
        
        # Filter to only include available languages
        available_priority = [lang for lang in priority_languages if lang in self.available_languages]
        
        if available_priority:
            # Use available priority languages
            lang_config = '+'.join(available_priority[:5])
            logger.info(f"🌍 Using multilingual OCR: {lang_config}")
            return lang_config
        else:
            logger.info("🌍 Using English-only OCR")
            return 'eng'

    def _minimal_clean_text(self, text):
        """Minimal text cleaning that preserves all characters"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

    def preservative_preprocessing(self, image_bytes):
        """Gentle preprocessing for multilingual support"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode != 'L':
                image = image.convert('L')
            
            # Very gentle enhancements
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Resize if image is too small
            if min(image.size) < 500:
                scale_factor = 500 / min(image.size)
                new_size = (int(image.size[0] * scale_factor), int(image.size[1] * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')

    async def extract_with_tesseract(self, image, lang, config):
        """Extract text with Tesseract with better error handling"""
        loop = asyncio.get_event_loop()
        try:
            text = await loop.run_in_executor(
                thread_pool,
                lambda: pytesseract.image_to_string(image, lang=lang, config=config, timeout=30)
            )
            return text
        except pytesseract.TesseractError as e:
            logger.warning(f"Tesseract error for {lang}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error during OCR for {lang}: {e}")
            return ""

    def get_supported_languages_info(self):
        """Get information about supported languages"""
        if not LANGUAGE_SUPPORT_AVAILABLE:
            return f"Basic support for {len(self.available_languages)} languages"
        
        supported_count = len(get_supported_languages())
        available_count = len(self.available_languages)
        
        return f"🌍 {supported_count}+ languages supported, {available_count} available in Tesseract"

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