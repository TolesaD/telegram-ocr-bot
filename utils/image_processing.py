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
        """Enhanced Tesseract extraction that preserves original formatting"""
        try:
            # Enhanced image preprocessing
            processed_image = self.enhanced_preprocess_image(image_bytes)
            
            # Check if language is available
            available_langs = self.get_tesseract_languages()
            if lang_code not in available_langs:
                logger.warning("Language %s not available, using English", lang_code)
                lang_code = 'eng'
            
            # Use configuration that preserves layout and formatting
            preserve_config = '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c tessedit_create_text=1'
            
            try:
                # First try: Get detailed text with layout information
                data = pytesseract.image_to_data(
                    processed_image,
                    lang=lang_code,
                    config=preserve_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Reconstruct text with proper spacing and line breaks
                reconstructed_text = self.reconstruct_text_with_layout(data)
                
                if reconstructed_text and len(reconstructed_text.strip()) > 10:
                    logger.info("✅ Successfully extracted text with layout preservation")
                    return reconstructed_text
                    
            except Exception as e:
                logger.warning(f"Layout preservation failed: {e}")
            
            # Fallback: Simple extraction with better formatting
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang_code,
                config=preserve_config,
                timeout=30
            )
            
            # Enhanced cleaning that preserves paragraphs and spacing
            cleaned_text = self.preserve_formatting_clean_text(text)
            
            if not cleaned_text:
                return "🔍 No readable text found. Please try:\n• Clearer, well-lit images\n• Better focus and contrast\n• Straight, non-blurry photos\n• Crop to text area"
            
            return cleaned_text
            
        except Exception as e:
            raise Exception(f"Tesseract error: {e}")
    
    def reconstruct_text_with_layout(self, data):
        """Reconstruct text preserving original layout and formatting"""
        try:
            lines = {}
            current_line_num = 0
            current_line_text = ""
            last_bottom = 0
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if not text:
                    continue
                
                conf = int(data['conf'][i])
                if conf < 30:  # Low confidence, skip
                    continue
                
                top = data['top'][i]
                bottom = top + data['height'][i]
                
                # Check if this is a new line
                if abs(top - last_bottom) > data['height'][i] * 0.5:
                    if current_line_text:
                        lines[current_line_num] = current_line_text.strip()
                        current_line_num += 1
                    current_line_text = text
                    last_bottom = bottom
                else:
                    # Same line, add space between words
                    if current_line_text:
                        current_line_text += " " + text
                    else:
                        current_line_text = text
                    last_bottom = max(last_bottom, bottom)
            
            # Add the last line
            if current_line_text:
                lines[current_line_num] = current_line_text.strip()
            
            # Join lines with proper line breaks
            result = '\n'.join([lines[key] for key in sorted(lines.keys())])
            
            return result if result.strip() else None
            
        except Exception as e:
            logger.error(f"Error reconstructing text layout: {e}")
            return None
    
    def preserve_formatting_clean_text(self, text):
        """Clean text while preserving original formatting, paragraphs, and spacing"""
        if not text:
            return ""
        
        # Split into lines and preserve meaningful whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.rstrip()  # Remove trailing whitespace but keep leading
            if line.strip():  # Keep non-empty lines
                cleaned_lines.append(line)
            else:
                # Preserve empty lines that separate paragraphs
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
        
        # Remove trailing empty lines
        while cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()
        
        # Join with original line breaks
        result = '\n'.join(cleaned_lines)
        
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