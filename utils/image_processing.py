import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import io
import config
import logging
import os
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    
    @staticmethod
    def setup_tesseract_path():
        """Set Tesseract path for both Windows and Linux"""
        # Common Tesseract paths
        possible_paths = [
            # Windows paths
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            # Linux paths (PythonAnywhere)
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"✅ Tesseract path set to: {path}")
                return True
        
        logger.error("❌ Tesseract not found in common locations")
        return False
    
    @staticmethod
    def check_tesseract_availability():
        """Check if Tesseract is available"""
        try:
            if ImageProcessor.setup_tesseract_path():
                version = pytesseract.get_tesseract_version()
                logger.info(f"✅ Tesseract version: {version}")
                return True
        except Exception as e:
            logger.error(f"❌ Tesseract not available: {e}")
        return False
    
    @staticmethod
    def fast_preprocess_image(image_bytes):
        """Fast image preprocessing for better performance"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_size = image.size
            
            # Resize large images for faster processing (max 2000px on longest side)
            max_size = 2000
            if max(original_size) > max_size:
                ratio = max_size / max(original_size)
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"📐 Resized image from {original_size} to {new_size}")
            
            # Convert to grayscale (faster than color processing)
            if image.mode != 'L':
                image = image.convert('L')
            
            # Fast contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Reduced from 2.0 for speed
            
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return Image.open(io.BytesIO(image_bytes))
    
    @staticmethod
    async def extract_text_async(image_bytes, language='eng'):
        """Async text extraction with timeout handling"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            ImageProcessor.extract_text_fast, 
            image_bytes, 
            language
        )
    
    @staticmethod
    def extract_text_fast(image_bytes, language='eng'):
        """Fast text extraction with optimized settings"""
        try:
            if not ImageProcessor.setup_tesseract_path():
                raise Exception("Tesseract not configured")
            
            processed_image = ImageProcessor.fast_preprocess_image(image_bytes)
            
            # Fast Tesseract configuration for speed
            # oem 1: LSTM only (faster than default)
            # psm 6: Uniform block of text (good balance of speed/accuracy)
            custom_config = r'--oem 1 --psm 6 -c preserve_interword_spaces=1'
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image, 
                lang=language, 
                config=custom_config
            )
            
            cleaned_text = ImageProcessor.clean_extracted_text(text)
            
            if not cleaned_text:
                return "No readable text found in the image. Please try with a clearer image."
            
            logger.info(f"✅ Successfully extracted {len(cleaned_text)} characters")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise Exception(f"Failed to process image: {str(e)}")
    
    @staticmethod
    def clean_extracted_text(text):
        """Clean extracted text"""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            if len(stripped_line) > 1:  # Only keep lines with more than 1 character
                cleaned_lines.append(stripped_line)
        
        return '\n'.join(cleaned_lines)

# Test on import
print("🔍 Checking Tesseract installation...")
if ImageProcessor.check_tesseract_availability():
    print("✅ Tesseract OCR is properly configured!")
else:
    print("❌ Tesseract OCR configuration failed")