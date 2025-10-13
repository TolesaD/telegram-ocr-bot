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
        """Set Tesseract path for PythonAnywhere"""
        # PythonAnywhere has Tesseract pre-installed here
        pythonanywhere_paths = [
            '/usr/bin/tesseract',
        ]
        
        for path in pythonanywhere_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"✅ Tesseract path set to: {path}")
                return True
        
        # Fallback: try to find in PATH
        try:
            pytesseract.get_tesseract_version()
            logger.info("✅ Tesseract found in system PATH")
            return True
        except:
            logger.error("❌ Tesseract not found")
            return False
    
    @staticmethod
    def get_available_languages():
        """Get languages available on PythonAnywhere"""
        try:
            # These are typically available on PythonAnywhere
            common_languages = ['eng', 'spa', 'fra', 'deu', 'ita', 'por', 'rus', 'nld', 'tur']
            
            # Test each language to see if it's actually available
            available = []
            for lang in common_languages:
                if ImageProcessor.check_language_available(lang):
                    available.append(lang)
            
            logger.info(f"📋 Available languages: {available}")
            return available
            
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return ['eng']  # Fallback to English
    
    @staticmethod
    def check_language_available(language_code):
        """Check if a language is available by testing it"""
        try:
            if not ImageProcessor.setup_tesseract_path():
                return False
            
            # Create a simple test image
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (100, 30), color='white')
            d = ImageDraw.Draw(img)
            d.text((10, 10), "test", fill='black')
            
            # Try to use the language with a short timeout
            try:
                pytesseract.image_to_string(img, lang=language_code, timeout=2)
                return True
            except:
                return False
                
        except Exception as e:
            logger.error(f"Error checking language {language_code}: {e}")
            return False
    
    @staticmethod
    def fast_preprocess_image(image_bytes):
        """FAST image preprocessing"""
        try:
            start_time = time.time()
            
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Resize large images
            max_dimension = 1600
            if max(original_size) > max_dimension:
                ratio = max_dimension / max(original_size)
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Resized: {original_size} → {new_size}")
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.3)
            
            # Mild sharpening
            image = image.filter(ImageFilter.SHARPEN)
            
            processing_time = time.time() - start_time
            logger.info(f"⚡ Preprocessing completed in {processing_time:.2f}s")
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            return Image.open(io.BytesIO(image_bytes))
    
    @staticmethod
    async def extract_text_async(image_bytes, language='eng'):
        """Async text extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            ImageProcessor.extract_text_safe, 
            image_bytes, 
            language
        )
    
    @staticmethod
    def extract_text_safe(image_bytes, language='eng'):
        """Safe text extraction"""
        try:
            start_time = time.time()
            
            if not ImageProcessor.setup_tesseract_path():
                raise Exception("Tesseract not configured")
            
            # Check if language is available
            if not ImageProcessor.check_language_available(language):
                # Fallback to English if requested language isn't available
                if language != 'eng':
                    logger.warning(f"Language {language} not available, falling back to English")
                    language = 'eng'
            
            # Preprocess image
            processed_image = ImageProcessor.fast_preprocess_image(image_bytes)
            
            # Tesseract configuration
            custom_config = r'--oem 1 --psm 6 -c preserve_interword_spaces=1'
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image, 
                lang=language, 
                config=custom_config
            )
            
            total_time = time.time() - start_time
            logger.info(f"✅ OCR completed in {total_time:.2f}s (Language: {language})")
            
            cleaned_text = ImageProcessor.clean_extracted_text(text)
            
            if not cleaned_text:
                return "No readable text found. Please try a clearer image."
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise Exception(f"OCR Error: {str(e)}")
    
    @staticmethod
    def clean_extracted_text(text):
        """Clean extracted text"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if len(stripped_line) > 1 and any(c.isalnum() for c in stripped_line):
                cleaned_lines.append(stripped_line)
        
        return '\n'.join(cleaned_lines)

# Initialize on import
print("🔍 Initializing Tesseract on PythonAnywhere...")
if ImageProcessor.setup_tesseract_path():
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR v{version} is ready!")
        available_langs = ImageProcessor.get_available_languages()
        print(f"📍 Available languages: {available_langs}")
    except Exception as e:
        print(f"❌ Tesseract initialization failed: {e}")
else:
    print("❌ Tesseract not found")