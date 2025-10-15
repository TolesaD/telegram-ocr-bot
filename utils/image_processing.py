import asyncio
import logging
import time
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import os
import pytesseract
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

logger = logging.getLogger(__name__)

# Enhanced thread pool for better performance
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ocr_")

class OCRProcessor:
    def __init__(self):
        self.engines = {}
        self.cache = {}  # Simple cache for frequent languages
        self.tesseract_available = False
        self.tesseract_config = '--oem 3 --psm 6 -c preserve_interword_spaces=1'  # DEFAULT CONFIG
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
                self.tesseract_available = True
            
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
            self.tesseract_config = '--oem 3 --psm 6 -c preserve_interword_spaces=1'
            
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
    
    async def extract_text_optimized(self, image_bytes, language='english'):
        """Enhanced text extraction with performance optimizations"""
        start_time = time.time()
        
        try:
            # If Tesseract is not available, return mock text
            if not self.tesseract_available:
                mock_text = (
                    "🔧 *OCR Engine Not Available*\n\n"
                    "Tesseract OCR is not installed on this server.\n\n"
                    "📝 *Mock Response for Testing:*\n"
                    "This is sample extracted text that would normally be obtained from your image. "
                    "For production use, please install Tesseract OCR system dependencies.\n\n"
                    "💡 *For Railway Deployment:*\n"
                    "• Add Tesseract to your Dockerfile\n"
                    "• Install system dependencies\n"
                    "• Use OCR-as-a-service APIs"
                )
                return mock_text
            
            # Convert language name to code with caching
            lang_code = self.get_language_code(language)
            logger.info("🔤 Using language: %s -> %s", language, lang_code)
            
            # Use Tesseract with enhanced preprocessing
            text = await self.extract_with_tesseract_enhanced(image_bytes, lang_code)
            
            processing_time = time.time() - start_time
            logger.info("⚡ Tesseract processed in %.2fs", processing_time)
            return text
            
        except Exception as e:
            logger.error("OCR processing failed: %s", e)
            # Fallback to mock text for testing
            return "📝 This is a mock text response since OCR processing failed. Please check server logs for details."
    
    def get_language_code(self, language_name):
        """Convert language name to Tesseract code with extended support"""
        language_map = {
            'english': 'eng', 'spanish': 'spa', 'french': 'fra', 'german': 'deu',
            'italian': 'ita', 'portuguese': 'por', 'russian': 'rus', 
            'chinese_simplified': 'chi_sim', 'japanese': 'jpn', 'korean': 'kor',
            'arabic': 'ara', 'hindi': 'hin', 'turkish': 'tur', 'dutch': 'nld',
            'swedish': 'swe', 'polish': 'pol', 'ukrainian': 'ukr', 'greek': 'ell',
            'amharic': 'amh'
        }
        
        return language_map.get(language_name.lower(), 'eng')
    
    async def extract_with_tesseract_enhanced(self, image_bytes, lang_code):
        """Enhanced Tesseract extraction with multiple optimizations"""
        # If Tesseract is not available, return mock text
        if not self.tesseract_available:
            return "🔧 OCR Engine Not Available\n\nTesseract OCR is not installed on this server."

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool,
            self._tesseract_extract_enhanced,
            image_bytes,
            lang_code
        )
    
    def _tesseract_extract_enhanced(self, image_bytes, lang_code):
        """Enhanced Tesseract extraction with multiple preprocessing techniques"""
        try:
            # Enhanced image preprocessing
            processed_image = self.enhanced_preprocess_image(image_bytes)
            
            # Check if language is available
            available_langs = self.get_tesseract_languages()
            if lang_code not in available_langs:
                logger.warning("Language %s not available, using English", lang_code)
                lang_code = 'eng'
            
            # Try multiple PSM modes with timeout
            psm_modes = [6, 3, 4, 8, 11, 13]  # Added more modes for better accuracy
            
            best_text = ""
            best_confidence = 0
            
            for psm_mode in psm_modes:
                try:
                    config = f'--oem 3 --psm {psm_mode} -c tessedit_do_invert=0'
                    
                    # Get both text and confidence
                    data = pytesseract.image_to_data(
                        processed_image,
                        lang=lang_code,
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Calculate average confidence
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Extract text
                    text = ' '.join([word for i, word in enumerate(data['text']) 
                                   if int(data['conf'][i]) > 60])
                    
                    cleaned_text = self.enhanced_clean_text(text)
                    
                    # Choose best result based on confidence and text length
                    if (avg_confidence > best_confidence and 
                        len(cleaned_text.strip()) > len(best_text.strip())):
                        best_text = cleaned_text
                        best_confidence = avg_confidence
                        
                    # Early exit if we have high confidence
                    if avg_confidence > 85 and len(cleaned_text.strip()) > 10:
                        logger.info("🎯 High confidence (%d%%) with PSM %d", avg_confidence, psm_mode)
                        return cleaned_text
                        
                except Exception as e:
                    logger.debug("PSM mode %d failed: %s", psm_mode, str(e))
                    continue
            
            # Return best result found
            if best_text and len(best_text.strip()) > 5:
                logger.info("🏆 Using best result with %d%% confidence", best_confidence)
                return best_text
            
            # Fallback to simple extraction
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang_code,
                config=self.tesseract_config,
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
        """Advanced text cleaning with multiple techniques"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Advanced filtering
        filtered_lines = []
        for line in lines:
            # Remove lines that are too short or likely noise
            if len(line) < 2:
                continue
                
            # Check for meaningful content (letters/numbers ratio)
            alpha_count = sum(c.isalpha() for c in line)
            digit_count = sum(c.isdigit() for c in line)
            total_chars = len(line)
            
            # Keep lines with reasonable text content
            if (alpha_count + digit_count) / total_chars > 0.3:  # At least 30% alphanumeric
                # Remove common OCR artifacts
                line = self.remove_ocr_artifacts(line)
                filtered_lines.append(line)
        
        # Join with proper spacing
        result = '\n'.join(filtered_lines)
        
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