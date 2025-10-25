# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import os
import pytesseract
import subprocess
import shutil
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")

# Import your comprehensive language support
try:
    from ocr_engine.language_support import (
        TESSERACT_LANGUAGES, SCRIPT_FAMILIES, get_script_family,
        get_tesseract_code, get_ocr_config, detect_script_from_text,
        get_fallback_strategy, clean_ocr_text, validate_ocr_result,
        detect_primary_language, get_language_confidence,
        get_supported_languages, get_language_name,
        detect_language_with_fallback, is_amharic_character
    )
    LANGUAGE_SUPPORT_AVAILABLE = True
    logger.info("✅ Enhanced language support loaded")
except ImportError as e:
    LANGUAGE_SUPPORT_AVAILABLE = False
    logger.warning(f"❌ Language support module not available: {e}")

class OCRProcessor:
    def __init__(self):
        self.setup_tesseract()
        self.available_languages = []
        self._load_available_languages()
        self.easyocr_available = self._check_easyocr()
    
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

    def _check_easyocr(self):
        """Check if EasyOCR is available with better Windows compatibility"""
        try:
            # Skip EasyOCR on Windows if there are DLL issues
            if os.name == 'nt':  # Windows
                logger.info("🔄 Skipping EasyOCR on Windows due to compatibility issues")
                return False
                
            import easyocr
            # Initialize with common languages for better performance
            self.easyocr_reader = easyocr.Reader(
                ['en', 'ch_sim', 'ja', 'ko', 'hi', 'ar', 'am'], 
                gpu=False  # CPU mode for better compatibility
            )
            logger.info("✅ EasyOCR initialized successfully")
            return True
        except ImportError:
            logger.warning("❌ EasyOCR not available, using Tesseract only")
            return False
        except Exception as e:
            logger.warning(f"❌ EasyOCR initialization failed: {e}")
            return False

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

    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with multiple OCR engines and better preprocessing"""
        start_time = time.time()
        
        try:
            # Enhanced preprocessing for blurry images
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.enhanced_preprocessing,
                image_bytes
            )
            
            # Try multiple OCR strategies with enhanced language detection
            text = await self.multi_engine_ocr(processed_image, image_bytes)
            
            processing_time = time.time() - start_time
            
            if not text or len(text.strip()) < 2:
                logger.warning("❌ No text extracted or text too short")
                return "🔍 No readable text found. Please try a clearer image with better contrast."
            
            # Enhanced text cleaning with language detection
            if LANGUAGE_SUPPORT_AVAILABLE:
                detected_lang, confidence = detect_language_with_fallback(text)
                cleaned_text = clean_ocr_text(text, detected_lang)
                
                # Validate the result
                is_valid, validation_msg = validate_ocr_result(cleaned_text, detected_lang)
                if not is_valid:
                    logger.warning(f"OCR validation failed: {validation_msg}")
                    # Try alternative OCR engine if available and result is poor
                    if self.easyocr_available and len(cleaned_text.strip()) < 20:
                        logger.info("🔄 Trying EasyOCR as fallback due to poor Tesseract result...")
                        easyocr_text = await self.extract_with_easyocr(image_bytes)
                        if easyocr_text and len(easyocr_text.strip()) > len(cleaned_text.strip()):
                            cleaned_text = easyocr_text
                            logger.info("✅ EasyOCR provided better results")
            else:
                cleaned_text = self._minimal_clean_text(text)
            
            logger.info(f"✅ OCR completed in {processing_time:.2f}s")
            logger.info(f"📝 Extracted {len(cleaned_text)} characters")
            
            if LANGUAGE_SUPPORT_AVAILABLE:
                detected_lang, confidence = detect_language_with_fallback(cleaned_text)
                lang_name = get_language_name(detected_lang)
                logger.info(f"🌍 Detected language: {lang_name} ({detected_lang}) with confidence {confidence:.2f}")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            logger.error(f"Full error details:", exc_info=True)
            return "❌ Error processing image. Please try again with a different image."

    def enhanced_preprocessing(self, image_bytes):
        """Enhanced preprocessing for blurry and low-quality images"""
        try:
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            # Enhanced preprocessing pipeline
            processed = self._apply_advanced_preprocessing(img_array)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(processed)
            
            # Resize if image is too small (improves OCR for small text)
            if min(processed_image.size) < 600:
                scale_factor = 600 / min(processed_image.size)
                new_size = (int(processed_image.size[0] * scale_factor), 
                           int(processed_image.size[1] * scale_factor))
                processed_image = processed_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to grayscale for Tesseract
            processed_image = processed_image.convert('L')
            
            logger.info("✅ Enhanced preprocessing completed")
            return processed_image
            
        except Exception as e:
            logger.error(f"Enhanced preprocessing failed: {e}")
            # Fallback to basic preprocessing
            return Image.open(io.BytesIO(image_bytes)).convert('L')

    def _apply_advanced_preprocessing(self, img_array):
        """Apply advanced image preprocessing techniques for blurry images"""
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Step 1: Noise reduction for blurry images
        denoised = cv2.medianBlur(gray, 3)
        
        # Step 2: Contrast enhancement using CLAHE (Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        contrast_enhanced = clahe.apply(denoised)
        
        # Step 3: Sharpening filter to enhance text edges in blurry images
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(contrast_enhanced, -1, kernel)
        
        # Step 4: Binarization using adaptive threshold (better for varying lighting)
        binary = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Step 5: Morphological operations to clean up the image
        kernel = np.ones((1,1), np.uint8)  # Smaller kernel to preserve details
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned

    async def multi_engine_ocr(self, processed_image, original_image_bytes):
        """Multi-engine OCR with smart fallback strategies"""
        strategies = []
        
        # Get optimized language first
        optimized_lang = self.get_optimized_language_config(processed_image) if LANGUAGE_SUPPORT_AVAILABLE else 'eng'
        
        # Strategy 1: Use the optimized language first
        strategies.append(('tesseract', optimized_lang, '--oem 3 --psm 6 -c preserve_interword_spaces=1'))
        
        # Strategy 2: Always try Amharic as a secondary option if available
        if 'amh' in self.available_languages and optimized_lang != 'amh':
            strategies.append(('tesseract', 'amh', '--oem 3 --psm 6 -c preserve_interword_spaces=1'))
        
        # Strategy 3: Try multilingual combinations
        if optimized_lang == 'eng' and 'amh' in self.available_languages:
            strategies.append(('tesseract', 'eng+amh', '--oem 3 --psm 6 -c preserve_interword_spaces=1'))
        elif optimized_lang == 'amh' and 'eng' in self.available_languages:
            strategies.append(('tesseract', 'amh+eng', '--oem 3 --psm 6 -c preserve_interword_spaces=1'))
        
        # Strategy 4: Try different PSM modes for better structure detection
        strategies.extend([
            ('tesseract', optimized_lang, '--oem 3 --psm 4 -c preserve_interword_spaces=1'),  # Single column
            ('tesseract', optimized_lang, '--oem 3 --psm 3 -c preserve_interword_spaces=1'),  # Fully automatic
        ])
        
        # Strategy 5: EasyOCR if available (better for Chinese/Japanese/Korean and blurry images)
        if self.easyocr_available:
            strategies.append(('easyocr', 'multi', ''))
        
        # Strategy 6: Universal fallback strategies
        strategies.extend([
            ('tesseract', 'eng', '--oem 3 --psm 6 -c preserve_interword_spaces=1'),
        ])
        
        best_text = ""
        best_confidence = 0
        best_engine = "none"
        
        for i, (engine, lang, config) in enumerate(strategies):
            try:
                logger.info(f"🔧 Trying {engine} strategy {i+1}: {lang} with {config}")
                
                if engine == 'tesseract':
                    text = await self.extract_with_tesseract(processed_image, lang, config)
                else:  # easyocr
                    text = await self.extract_with_easyocr(original_image_bytes)
                
                if text and text.strip():
                    # Calculate confidence
                    confidence = self.calculate_text_confidence(text, lang)
                    
                    # Smart confidence adjustment for Amharic
                    if 'amh' in lang:
                        if self._is_amharic_text(text):
                            confidence = min(confidence + 0.3, 1.0)  # Increased boost
                            logger.info(f"📈 Boosted confidence for meaningful Amharic text: {confidence:.2f}")
                        else:
                            # If using Amharic but no meaningful Amharic letters found, reduce confidence
                            confidence = confidence * 0.6  # Increased reduction
                            logger.info(f"📉 Reduced confidence for Amharic without letters: {confidence:.2f}")
                    
                    # Special case: if optimized language was English but we got Amharic text with Amharic OCR, boost confidence
                    if optimized_lang == 'eng' and 'amh' in lang and self._is_amharic_text(text):
                        confidence = min(confidence + 0.4, 1.0)  # Boost for correct Amharic detection
                        logger.info(f"🎯 Significant confidence boost for Amharic detection on Amharic image: {confidence:.2f}")
                    
                    if confidence > best_confidence:
                        best_text = text
                        best_confidence = confidence
                        best_engine = engine
                        logger.info(f"✅ {engine} strategy {i+1} confidence: {confidence:.2f}")
                    
                    # Early exit for high confidence results
                    if confidence > 0.9:  # Increased threshold
                        logger.info(f"🎯 High confidence result with {engine} strategy {i+1}")
                        break
                        
            except Exception as e:
                logger.warning(f"❌ {engine} strategy {i+1} failed: {e}")
                continue
        
        logger.info(f"🏆 Best result from {best_engine} with confidence {best_confidence:.2f}")
        return best_text

    def get_optimized_language_config(self, processed_image=None):
        """Get optimized language configuration using enhanced language support"""
        if not LANGUAGE_SUPPORT_AVAILABLE:
            return self.get_multilingual_config()
        
        # Quick OCR to detect script and language
        detected_script = 'Latin'  # Default
        
        if processed_image:
            try:
                # First, try a very quick English detection with minimal characters
                eng_text = pytesseract.image_to_string(
                    processed_image, 
                    lang='eng',  # Try English first
                    config='--psm 6 --oem 3 -c min_characters_to_try=1 -c tessedit_write_images=false'
                )
                
                # Enhanced English detection with stricter criteria
                if eng_text and len(eng_text.strip()) > 5:
                    # Count actual English letters and common English words
                    english_letters = sum(1 for c in eng_text if c.isalpha() and c.isascii())
                    total_chars = len(eng_text.strip())
                    
                    # Check for common English words to confirm it's really English
                    common_english_words = ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our']
                    text_lower = eng_text.lower()
                    english_word_count = sum(1 for word in common_english_words if word in text_lower)
                    
                    english_ratio = english_letters / total_chars if total_chars > 0 else 0
                    
                    # Very strict criteria for English detection
                    if english_ratio > 0.85 or (english_ratio > 0.7 and english_word_count >= 2):
                        logger.info(f"🔍 Confidently detected English text with {english_letters}/{total_chars} English chars and {english_word_count} common words")
                        return 'eng'
                
                # Then try Amharic detection with very strict criteria
                amh_text = pytesseract.image_to_string(
                    processed_image, 
                    lang='amh',  # Try Amharic
                    config='--psm 6 --oem 3 -c min_characters_to_try=1 -c tessedit_write_images=false'
                )
                
                # Very strict Amharic detection
                if amh_text and len(amh_text.strip()) > 8:
                    amharic_letters = sum(1 for c in amh_text if is_amharic_character(c) and not ('\u1369' <= c <= '\u1372'))
                    total_chars = len(amh_text.strip())
                    
                    # Count actual Amharic characters vs potential false positives
                    amharic_ratio = amharic_letters / total_chars if total_chars > 0 else 0
                    
                    # Very high threshold for Amharic to avoid false positives
                    if amharic_ratio > 0.4:  # 40% must be actual Amharic letters
                        logger.info(f"🔍 Confidently detected Amharic script with {amharic_letters}/{total_chars} Amharic letters (ratio: {amharic_ratio:.2f})")
                        return 'amh'
                    else:
                        logger.info(f"🔍 Amharic detection rejected: only {amharic_letters}/{total_chars} Amharic letters (ratio: {amharic_ratio:.2f})")
                
                # If both specific detections failed, try script detection
                quick_text = pytesseract.image_to_string(
                    processed_image, 
                    lang='osd',  # Orientation and script detection
                    config='--psm 0 --oem 3 -c min_characters_to_try=1 -c tessedit_write_images=false'
                )
                if quick_text:
                    detected_script = detect_script_from_text(quick_text)
                    logger.info(f"🔍 Detected script: {detected_script}")
                    
                    # If script is Ethiopic, prioritize Amharic
                    if detected_script == 'Ethiopic' and 'amh' in self.available_languages:
                        logger.info("🎯 Script detection suggests Amharic, using Amharic OCR")
                        return 'amh'
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
        
        # If we have Amharic available and detected Ethiopic script, prioritize it
        if detected_script == 'Ethiopic' and 'amh' in self.available_languages:
            if 'amh' not in tesseract_langs:
                tesseract_langs.insert(0, 'amh')
            else:
                # Move amh to front
                tesseract_langs.remove('amh')
                tesseract_langs.insert(0, 'amh')
        
        # If no languages found for script, use available languages
        if not tesseract_langs:
            tesseract_langs = self.available_languages[:3]  # Use first 3 available
        
        lang_config = '+'.join(tesseract_langs)
        logger.info(f"🌍 Using optimized language config: {lang_config} for {detected_script} script")
        return lang_config

    def _is_amharic_text(self, text):
        """Check if text contains meaningful Amharic characters (not just Geez numbers)"""
        if not text:
            return False
        
        # Count Amharic letters (excluding Geez numbers ፩-፲)
        amharic_letters = sum(1 for c in text if is_amharic_character(c) and not ('\u1369' <= c <= '\u1372'))
        
        # Count Geez numbers separately
        geez_numbers = sum(1 for c in text if '\u1369' <= c <= '\u1372')
        
        # Count English letters to check for false positives
        english_letters = sum(1 for c in text if c.isalpha() and c.isascii())
        
        total_chars = len(text.strip())
        
        if total_chars == 0:
            return False
        
        amharic_letter_ratio = amharic_letters / total_chars
        geez_number_ratio = geez_numbers / total_chars
        english_ratio = english_letters / total_chars
        
        # Only boost confidence if there are actual Amharic letters and minimal English
        has_meaningful_amharic = amharic_letter_ratio > 0.25 and english_ratio < 0.3  # Higher threshold, less English
        
        logger.info(f"🔤 Amharic analysis - Letters: {amharic_letters}, Numbers: {geez_numbers}, English: {english_letters}, Total: {total_chars}")
        logger.info(f"🔤 Ratios - Amharic: {amharic_letter_ratio:.2f}, Numbers: {geez_number_ratio:.2f}, English: {english_ratio:.2f}")
        
        return has_meaningful_amharic

    async def extract_with_easyocr(self, image_bytes):
        """Extract text using EasyOCR (better for CJK languages and blurry images)"""
        if not self.easyocr_available:
            return ""
        
        try:
            import easyocr
            loop = asyncio.get_event_loop()
            
            # Read image directly from bytes
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("❌ Failed to decode image for EasyOCR")
                return ""
            
            # Perform OCR with paragraph detection
            results = await loop.run_in_executor(
                thread_pool,
                lambda: self.easyocr_reader.readtext(
                    image, 
                    paragraph=True,  # Group text into paragraphs
                    detail=0,  # Return only text, no bounding boxes or confidence
                    batch_size=4  # Process in batches for better performance
                )
            )
            
            # Combine results with proper spacing
            text = '\n'.join([str(item) for item in results if item])
            
            logger.info(f"🔤 EasyOCR extracted {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return ""

    def calculate_text_confidence(self, text, lang_used):
        """Enhanced confidence score calculation for OCR result"""
        if not text:
            return 0
        
        text_length = len(text.strip())
        if text_length < 3:
            return 0
        
        # Base confidence on text length (more lenient)
        length_confidence = min(text_length / 30.0, 1.0)
        
        # Character diversity
        unique_chars = len(set(text))
        diversity_confidence = min(unique_chars / 10.0, 1.0)
        
        # Language-specific confidence
        if LANGUAGE_SUPPORT_AVAILABLE:
            detected_lang, lang_confidence = detect_language_with_fallback(text)
            
            # HEAVY penalties for language mismatches
            if 'amh' in lang_used and detected_lang == 'en':
                lang_confidence = lang_confidence * 0.1  # Very heavy penalty for using Amharic on English text
                logger.info(f"⚠️  VERY HEAVY penalty for language mismatch (Amharic OCR on English text): {lang_confidence:.2f}")
            elif 'eng' in lang_used and detected_lang == 'am':
                lang_confidence = lang_confidence * 0.3  # Heavy penalty for using English on Amharic text
                logger.info(f"⚠️  Heavy penalty for language mismatch (English OCR on Amharic text): {lang_confidence:.2f}")
            
            # Bonus for correct language detection
            if ('amh' in lang_used and detected_lang == 'am') or ('eng' in lang_used and detected_lang == 'en'):
                lang_confidence = min(lang_confidence + 0.2, 1.0)  # Bonus for correct language
                logger.info(f"🎯 Bonus for correct language detection: {lang_confidence:.2f}")
        else:
            lang_confidence = 0.5
        
        # Check for meaningful word patterns
        word_confidence = self._calculate_word_confidence(text)
        
        # Check for garbage patterns (repeating characters, etc.)
        garbage_penalty = self._calculate_garbage_penalty(text)
        
        # Combined confidence with weights
        total_confidence = (
            length_confidence * 0.20 + 
            diversity_confidence * 0.20 + 
            lang_confidence * 0.40 +  # Increased weight for language confidence
            word_confidence * 0.20 -
            garbage_penalty
        )
        
        return max(0.0, min(1.0, total_confidence))

    def _calculate_word_confidence(self, text):
        """Calculate confidence based on word patterns"""
        words = text.split()
        if not words:
            return 0
        
        # Count words with reasonable length (2+ characters)
        valid_words = sum(1 for word in words if len(word) >= 2)
        
        return valid_words / len(words) if words else 0

    def _calculate_garbage_penalty(self, text):
        """Calculate penalty for garbage text patterns"""
        penalty = 0.0
        
        # Penalize repeating characters (like "eeeeee", "------")
        for char in set(text):
            if text.count(char) > len(text) * 0.5:  # If one char is >50% of text
                penalty += 0.3
        
        # Penalize too many special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars > len(text) * 0.6:  # If >60% special chars
            penalty += 0.4
        
        return min(penalty, 0.5)  # Cap penalty at 0.5

    def get_multilingual_config(self):
        """Get optimal language configuration based on available languages"""
        # Enhanced priority languages including CJK
        priority_languages = ['eng', 'amh', 'chi_sim', 'chi_tra', 'jpn', 'kor', 
                             'ara', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'hin']
        
        # Filter to only include available languages
        available_priority = [lang for lang in priority_languages if lang in self.available_languages]
        
        if available_priority:
            # Use available priority languages (limit to 4 for performance)
            lang_config = '+'.join(available_priority[:4])
            logger.info(f"🌍 Using multilingual OCR: {lang_config}")
            return lang_config
        else:
            logger.info("🌍 Using English-only OCR")
            return 'eng'

    def _minimal_clean_text(self, text):
        """Minimal text cleaning that preserves all characters and structure"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Preserve original line structure, only clean excessive internal whitespace
            cleaned_line = ' '.join(line.split())
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

    async def extract_with_tesseract(self, image, lang, config):
        """Enhanced Tesseract extraction with better error handling"""
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
            logger.error(f"Unexpected error during Tesseract OCR for {lang}: {e}")
            return ""

    def get_supported_languages_info(self):
        """Get information about supported languages"""
        if not LANGUAGE_SUPPORT_AVAILABLE:
            return f"Basic support for {len(self.available_languages)} languages"
        
        supported_count = len(get_supported_languages())
        available_count = len(self.available_languages)
        
        engines = "Tesseract" + (" + EasyOCR" if self.easyocr_available else "")
        
        return f"🌍 {supported_count}+ languages supported, {available_count} available ({engines})"

# Create global instance AFTER the class is fully defined
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