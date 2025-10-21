# utils/image_processing.py
import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
import pytesseract
import subprocess
from concurrent.futures import ThreadPoolExecutor

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
            
            # Test Amharic specifically
            self._test_amharic_language()
            
            return True
        except Exception as e:
            logger.error(f"Tesseract initialization failed: {e}")
            return False
    
    def _test_amharic_language(self):
        """Test if Amharic language pack is working correctly"""
        try:
            # Create a simple test image with Amharic-like patterns
            test_image = Image.new('RGB', (200, 50), color='white')
            
            # Test basic Amharic extraction
            test_text = pytesseract.image_to_string(test_image, lang='amh', config='--psm 8')
            logger.info("✅ Amharic language pack test completed")
            
            # List available Amharic-related language files
            self._check_amharic_language_files()
            
        except Exception as e:
            logger.error(f"❌ Amharic language test failed: {e}")
    
    def _check_amharic_language_files(self):
        """Check what Amharic language files are available"""
        try:
            tessdata_paths = [
                '/usr/share/tesseract-ocr/5/tessdata',
                '/usr/share/tesseract-ocr/4.00/tessdata',
                '/usr/share/tesseract-ocr/tessdata'
            ]
            
            for tessdata_path in tessdata_paths:
                if os.path.exists(tessdata_path):
                    logger.info(f"📁 Checking tessdata path: {tessdata_path}")
                    files = os.listdir(tessdata_path)
                    amharic_files = [f for f in files if 'amh' in f.lower()]
                    if amharic_files:
                        logger.info(f"🔤 Amharic files found: {amharic_files}")
                    else:
                        logger.warning(f"❌ No Amharic files found in {tessdata_path}")
        except Exception as e:
            logger.error(f"Error checking Amharic files: {e}")
    
    def _find_tesseract(self):
        """Find Tesseract installation path"""
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract', 
            '/bin/tesseract',
            '/app/bin/tesseract'
        ]
        
        try:
            result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
            if result.returncode == 0:
                found_path = result.stdout.strip()
                if found_path and os.path.exists(found_path):
                    logger.info(f"🔍 Found Tesseract via 'which': {found_path}")
                    return found_path
        except:
            pass
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"🔍 Found Tesseract at: {path}")
                return path
        
        logger.error("❌ Could not find Tesseract in any known location")
        return None
    
    def _load_available_languages(self):
        """Load available Tesseract languages"""
        try:
            self.available_languages = pytesseract.get_languages()
            logger.info(f"📚 Found {len(self.available_languages)} available languages")
            
            # Specifically check for Amharic
            if 'amh' in self.available_languages:
                logger.info("✅ Amharic language is available")
            else:
                logger.error("❌ Amharic language is NOT available")
                
        except Exception as e:
            logger.error(f"Error loading available languages: {e}")
            self.available_languages = ['eng']
    
    def get_tesseract_code(self, language: str) -> str:
        """Convert language code to Tesseract code - MOVED HERE to avoid circular import"""
        mapping = {
            'en': 'eng', 'eng': 'eng', 'english': 'eng',
            'am': 'amh', 'amh': 'amh', 'amharic': 'amh',
            'ar': 'ara', 'ara': 'ara', 'arabic': 'ara',
            'zh': 'chi_sim', 'chi_sim': 'chi_sim', 'chinese': 'chi_sim',
            'ja': 'jpn', 'jpn': 'jpn', 'japanese': 'jpn',
            'ko': 'kor', 'kor': 'kor', 'korean': 'kor',
            'es': 'spa', 'spa': 'spa', 'spanish': 'spa',
            'fr': 'fra', 'fra': 'fra', 'french': 'fra',
            'de': 'deu', 'deu': 'deu', 'german': 'deu',
            'ru': 'rus', 'rus': 'rus', 'russian': 'rus'
        }
        return mapping.get(language.lower(), 'eng')
    
    def get_amharic_config(self) -> str:
        """Get optimized Tesseract config for Amharic - MOVED HERE to avoid circular import"""
        return '--oem 1 --psm 6 -c preserve_interword_spaces=1'
    
    def is_amharic_character(self, char: str) -> bool:
        """Check if character is in Amharic Unicode range - MOVED HERE to avoid circular import"""
        return '\u1200' <= char <= '\u137F'
    
    async def extract_text_optimized(self, image_bytes, language=None):
        """Enhanced text extraction with comprehensive Amharic support"""
        start_time = time.time()
        
        try:
            # Gentle preprocessing
            processed_image = await asyncio.get_event_loop().run_in_executor(
                thread_pool,
                self.preservative_preprocessing,
                image_bytes
            )
            
            # Smart language detection first
            detected_language = await self.detect_language_smart(processed_image)
            logger.info(f"🔍 Detected language: {detected_language}")
            
            # Extract text based on detected language
            if detected_language == 'am':
                text = await self.comprehensive_amharic_ocr(processed_image)
            else:
                text = await self.english_or_auto_ocr(processed_image, detected_language)
            
            processing_time = time.time() - start_time
            
            # Comprehensive text analysis
            if text:
                self._comprehensive_text_analysis(text, "FINAL OUTPUT")
            else:
                logger.warning("❌ No text extracted from image")
            
            if not text or len(text.strip()) < 2:
                return "🔍 No readable text found. Please try a clearer image."
            
            # Minimal cleaning to preserve all characters
            cleaned_text = self._minimal_clean_text(text)
            
            logger.info(f"✅ {detected_language.upper()} OCR completed in {processing_time:.2f}s")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return "❌ OCR processing failed. Please try again with a different image."
    
    async def comprehensive_amharic_ocr(self, processed_image):
        """Comprehensive Amharic OCR with multiple strategies and fallbacks"""
        strategies = [
            # Strategy 1: Standard Amharic
            ('amh', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            ('amh', '--oem 1 --psm 4 -c preserve_interword_spaces=1'),
            ('amh', '--oem 1 --psm 3 -c preserve_interword_spaces=1'),
            
            # Strategy 2: Amharic with different OEM
            ('amh', '--oem 2 --psm 6 -c preserve_interword_spaces=1'),
            ('amh', '--oem 3 --psm 6 -c preserve_interword_spaces=1'),
            
            # Strategy 3: Amharic with English fallback
            ('amh+eng', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            ('amh+eng', '--oem 1 --psm 4 -c preserve_interword_spaces=1'),
            
            # Strategy 4: Amharic vertical (if available)
            ('amh+amh_vert', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            
            # Strategy 5: Multi-language
            ('amh+eng+ara', '--oem 1 --psm 6 -c preserve_interword_spaces=1'),
            
            # Strategy 6: Script-specific
            ('amh', '--oem 1 --psm 6 -c tessedit_char_whitelist=፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼።፣፤፥፦፧፨፠፡።፣፤፥፦፧፨'),
        ]
        
        all_results = []
        
        for i, (lang, config) in enumerate(strategies):
            try:
                logger.info(f"🔧 Trying Amharic strategy {i+1}: {lang} with {config}")
                text = await self.extract_with_tesseract(processed_image, lang, config)
                
                if text and text.strip():
                    analysis = self._analyze_amharic_text(text)
                    analysis['strategy'] = f"{i+1}: {lang}"
                    analysis['config'] = config
                    analysis['text'] = text
                    all_results.append(analysis)
                    
                    logger.info(f"✅ Strategy {i+1} extracted {len(text)} chars, Amharic: {analysis['amharic_count']}, Confidence: {analysis['confidence']:.2f}")
                    
                    # If we get good results, log the actual text
                    if analysis['confidence'] > 0.3:
                        sample = text[:100].replace('\n', ' ')
                        logger.info(f"📝 Sample text: {sample}")
                
            except Exception as e:
                logger.warning(f"❌ Strategy {i+1} failed: {e}")
                continue
        
        # Choose the best result
        if all_results:
            # Sort by Amharic confidence
            all_results.sort(key=lambda x: x['confidence'], reverse=True)
            best_result = all_results[0]
            
            logger.info(f"🏆 Best strategy: {best_result['strategy']}")
            logger.info(f"🏆 Best confidence: {best_result['confidence']:.2f}")
            logger.info(f"🏆 Amharic characters: {best_result['amharic_count']}")
            logger.info(f"🏆 Total characters: {best_result['total_chars']}")
            
            # Log a sample of the best text
            sample = best_result['text'][:200].replace('\n', ' ')
            logger.info(f"🏆 Best text sample: {sample}")
            
            return best_result['text']
        else:
            logger.error("❌ All Amharic strategies failed")
            return await self._fallback_english_ocr(processed_image)
    
    def _analyze_amharic_text(self, text):
        """Comprehensive analysis of Amharic text"""
        if not text:
            return {'confidence': 0, 'amharic_count': 0, 'total_chars': 0}
        
        text = text.strip()
        total_chars = len(text)
        
        # Count Amharic characters (Ethiopic Unicode range)
        amharic_chars = [c for c in text if '\u1200' <= c <= '\u137F']
        amharic_count = len(amharic_chars)
        
        # Count other character types
        latin_chars = [c for c in text if c.isalpha() and c.isascii()]
        latin_count = len(latin_chars)
        
        # Calculate confidence
        if total_chars == 0:
            confidence = 0
        else:
            # Higher confidence if we have more Amharic characters
            amharic_ratio = amharic_count / total_chars
            # Bonus for having multiple Amharic characters
            diversity_bonus = min(len(set(amharic_chars)) / 10, 0.3)
            confidence = min(amharic_ratio + diversity_bonus, 1.0)
        
        return {
            'confidence': confidence,
            'amharic_count': amharic_count,
            'latin_count': latin_count,
            'total_chars': total_chars,
            'unique_amharic': len(set(amharic_chars)) if amharic_chars else 0
        }
    
    async def _fallback_english_ocr(self, processed_image):
        """Fallback to English OCR"""
        logger.info("🔄 Falling back to English OCR")
        try:
            text = await self.extract_with_tesseract(processed_image, 'eng', '--oem 3 --psm 6')
            if text and text.strip():
                logger.info("✅ English fallback successful")
                return text
        except Exception as e:
            logger.error(f"❌ English fallback also failed: {e}")
        
        return ""
    
    def _comprehensive_text_analysis(self, text, stage):
        """Comprehensive analysis of extracted text"""
        logger.info(f"🔍 {stage} - COMPREHENSIVE ANALYSIS:")
        logger.info(f"   Total length: {len(text)} characters")
        
        # Character type analysis
        amharic_chars = [c for c in text if '\u1200' <= c <= '\u137F']
        latin_chars = [c for c in text if c.isalpha() and c.isascii()]
        digit_chars = [c for c in text if c.isdigit()]
        space_chars = [c for c in text if c.isspace()]
        other_chars = [c for c in text if c not in amharic_chars + latin_chars + digit_chars + space_chars]
        
        logger.info(f"   Amharic characters: {len(amharic_chars)}")
        logger.info(f"   Latin characters: {len(latin_chars)}")
        logger.info(f"   Digits: {len(digit_chars)}")
        logger.info(f"   Spaces: {len(space_chars)}")
        logger.info(f"   Other characters: {len(other_chars)}")
        
        # Show unique Amharic characters
        if amharic_chars:
            unique_amharic = sorted(set(amharic_chars))
            logger.info(f"   Unique Amharic chars ({len(unique_amharic)}): {''.join(unique_amharic)}")
        
        # Show the actual text (first 500 characters)
        if text:
            sample = text[:500]
            # Replace newlines for logging
            sample_log = sample.replace('\n', '⏎')
            logger.info(f"   Text sample: {sample_log}")
        
        # Count lines and words
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        words = text.split()
        
        logger.info(f"   Lines: {len(lines)} (non-empty: {len(non_empty_lines)})")
        logger.info(f"   Words: {len(words)}")
    
    def _minimal_clean_text(self, text):
        """Minimal text cleaning that preserves all characters"""
        if not text:
            return ""
        
        # Simply normalize whitespace without removing any characters
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove excessive internal whitespace but preserve the line
            cleaned_line = ' '.join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        result = '\n'.join(cleaned_lines)
        return result
    
    async def detect_language_smart(self, processed_image):
        """Language detection focusing on Amharic"""
        try:
            # Quick test with Amharic first
            amh_text = await self.extract_with_tesseract(processed_image, 'amh', '--psm 6 --oem 1')
            amh_analysis = self._analyze_amharic_text(amh_text)
            
            # Test English
            eng_text = await self.extract_with_tesseract(processed_image, 'eng', '--psm 6 --oem 1')
            eng_latin_chars = sum(1 for c in eng_text if c.isalpha() and c.isascii())
            eng_confidence = eng_latin_chars / len(eng_text) if eng_text else 0
            
            logger.info(f"🔍 Language detection - Amharic: {amh_analysis['confidence']:.2f}, English: {eng_confidence:.2f}")
            
            # Prefer Amharic if we have reasonable confidence
            if amh_analysis['confidence'] > 0.1:
                return 'am'
            elif eng_confidence > 0.3:
                return 'en'
            else:
                return 'en'  # Default to English
                
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'en'
    
    async def english_or_auto_ocr(self, processed_image, detected_language):
        """OCR for English and other languages"""
        strategies = [
            ('eng', '--oem 3 --psm 6'),
            ('eng', '--oem 3 --psm 3'),
            ('osd', '--oem 3 --psm 3'),
        ]
        
        for lang, config in strategies:
            try:
                text = await self.extract_with_tesseract(processed_image, lang, config)
                if text and text.strip():
                    return text
            except Exception as e:
                continue
        
        return ""
    
    def preservative_preprocessing(self, image_bytes):
        """Gentle preprocessing"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            if image.mode != 'L':
                image = image.convert('L')
            
            # Very gentle enhancements
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return Image.open(io.BytesIO(image_bytes)).convert('L')
    
    async def extract_with_tesseract(self, image, lang, config):
        """Extract text with Tesseract"""
        loop = asyncio.get_event_loop()
        try:
            text = await loop.run_in_executor(
                thread_pool,
                lambda: pytesseract.image_to_string(image, lang=lang, config=config, timeout=60)
            )
            return text
        except Exception as e:
            logger.error(f"Tesseract extraction failed for {lang}: {e}")
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