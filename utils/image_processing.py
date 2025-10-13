import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import asyncio
import logging
import os
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    
    @staticmethod
    def setup_tesseract_path():
        """Set Tesseract path - optimized for Windows"""
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            '/usr/bin/tesseract',  # Linux
            '/usr/local/bin/tesseract',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"✅ Tesseract path: {path}")
                return True
        
        # Try system PATH
        try:
            pytesseract.get_tesseract_version()
            logger.info("✅ Tesseract found in PATH")
            return True
        except:
            logger.error("❌ Tesseract not found")
            return False
    
    @staticmethod
    def check_language_available(language_code):
        """Check if a language is available in Tesseract"""
        try:
            if not ImageProcessor.setup_tesseract_path():
                return False
            
            # Get Tesseract data path
            tesseract_cmd = pytesseract.pytesseract.tesseract_cmd
            tesseract_dir = os.path.dirname(tesseract_cmd)
            tessdata_dir = os.path.join(tesseract_dir, 'tessdata')
            
            # Check if language file exists
            lang_file = os.path.join(tessdata_dir, f'{language_code}.traineddata')
            if os.path.exists(lang_file):
                logger.info(f"✅ Language {language_code} is available")
                return True
            else:
                logger.warning(f"❌ Language {language_code} not found at {lang_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking language {language_code}: {e}")
            return False
    
    @staticmethod
    def fast_preprocess_image(image_bytes):
        """FAST image preprocessing without OpenCV dependencies"""
        try:
            start_time = time.time()
            
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # FAST Resize - larger images slow down OCR significantly
            max_dimension = 1600
            if max(original_size) > max_dimension:
                ratio = max_dimension / max(original_size)
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Resized: {original_size} → {new_size}")
            
            # Convert to grayscale (faster processing)
            if image.mode != 'L':
                image = image.convert('L')
            
            # FAST contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            
            # Mild sharpening
            image = image.filter(ImageFilter.SHARPEN)
            
            processing_time = time.time() - start_time
            logger.info(f"⚡ Preprocessing completed in {processing_time:.2f}s")
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing error, using original: {e}")
            return Image.open(io.BytesIO(image_bytes))
    
    @staticmethod
    async def extract_text_async(image_bytes, language='eng'):
        """Async text extraction with better error handling"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            ImageProcessor.extract_text_safe, 
            image_bytes, 
            language
        )
    
    @staticmethod
    def extract_text_safe(image_bytes, language='eng'):
        """Safe text extraction with language availability check"""
        try:
            start_time = time.time()
            
            if not ImageProcessor.setup_tesseract_path():
                raise Exception("Tesseract not configured")
            
            # Check if language is available
            if not ImageProcessor.check_language_available(language):
                raise Exception(f"Language '{language}' is not installed. Please install the language pack or try a different language.")
            
            # Preprocess image
            processed_image = ImageProcessor.fast_preprocess_image(image_bytes)
            
            # OPTIMIZED Tesseract configuration for SPEED
            custom_config = r'--oem 1 --psm 6 -c preserve_interword_spaces=1 tessedit_do_invert=0'
            
            # Extract text with optimized settings
            text = pytesseract.image_to_string(
                processed_image, 
                lang=language, 
                config=custom_config
            )
            
            total_time = time.time() - start_time
            logger.info(f"✅ OCR completed in {total_time:.2f}s")
            
            cleaned_text = ImageProcessor.clean_extracted_text(text)
            
            if not cleaned_text:
                return "No readable text found. Try: better lighting, clearer text, higher contrast."
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            # Provide more helpful error messages
            if "language" in str(e).lower() and "not installed" in str(e).lower():
                raise Exception(f"Language '{language}' is not installed. Please try English or install the language pack.")
            elif "tesseract" in str(e).lower():
                raise Exception(f"Tesseract error: {str(e)}")
            else:
                raise Exception(f"OCR processing failed: {str(e)}")
    
    @staticmethod
    def clean_extracted_text(text):
        """Fast text cleaning"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            # Only keep lines with meaningful content
            if len(stripped_line) > 1 and any(c.isalnum() for c in stripped_line):
                cleaned_lines.append(stripped_line)
        
        return '\n'.join(cleaned_lines)

# Test on import
print("🔍 Checking Tesseract installation...")
if ImageProcessor.setup_tesseract_path():
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR v{version} is ready!")
        
        # Test available languages
        print("🔍 Checking available languages...")
        available_langs = ['eng', 'spa', 'fra', 'deu', 'ita', 'por']  # Basic languages
        for lang in available_langs:
            if ImageProcessor.check_language_available(lang):
                print(f"   ✅ {lang} available")
            else:
                print(f"   ❌ {lang} not available")
                
    except Exception as e:
        print(f"❌ Tesseract found but not working: {e}")
else:
    print("❌ Tesseract OCR configuration failed")