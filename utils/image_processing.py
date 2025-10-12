import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import io
import config  # Import config directly
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    
    @staticmethod
    def setup_tesseract_path():
        """Set Tesseract path to the exact location you found"""
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"✅ Tesseract path set to: {tesseract_path}")
            return True
        else:
            logger.error(f"❌ Tesseract not found at: {tesseract_path}")
            return False
    
    @staticmethod
    def check_tesseract_availability():
        """Check if Tesseract is available and properly installed"""
        try:
            # First, setup the tesseract path
            if not ImageProcessor.setup_tesseract_path():
                return False
            
            # Now check if it works
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract version: {version}")
            
            # Check available languages
            try:
                available_langs = pytesseract.get_languages()
                logger.info(f"✅ Available languages: {available_langs}")
            except:
                logger.warning("⚠️ Could not retrieve language list")
                
            return True
        except Exception as e:
            logger.error(f"❌ Tesseract not available: {e}")
            return False
    
    @staticmethod
    def preprocess_image(image_bytes):
        """Preprocess image for better OCR results"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get image size for logging
            width, height = image.size
            logger.info(f"📏 Image size: {width}x{height}")
            
            # Simple preprocessing - start with basic operations
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            logger.info("✅ Image preprocessing completed")
            return image
            
        except Exception as e:
            logger.error(f"❌ Error in image preprocessing: {e}")
            # Return original image if preprocessing fails
            try:
                return Image.open(io.BytesIO(image_bytes))
            except:
                raise Exception(f"Failed to process image: {e}")
    
    @staticmethod
    def extract_text(image_bytes, language='eng'):
        """Extract text from image using Tesseract OCR"""
        try:
            # Check if Tesseract is available
            if not ImageProcessor.check_tesseract_availability():
                raise Exception("Tesseract OCR is not configured properly.")
            
            # Preprocess image
            processed_image = ImageProcessor.preprocess_image(image_bytes)
            
            # Configure Tesseract for better accuracy
            custom_config = r'--oem 3 --psm 6'
            
            # Extract text
            logger.info(f"🔤 Extracting text with language: {language}")
            text = pytesseract.image_to_string(processed_image, lang=language, config=custom_config)
            
            # Clean up the extracted text
            cleaned_text = ImageProcessor.clean_extracted_text(text)
            
            if not cleaned_text:
                logger.warning("❌ No text extracted from image")
                return "No readable text found in the image. Please try with:\n• Better lighting\n• Higher contrast\n• Clearer text\n• Less background noise"
            
            logger.info(f"✅ Successfully extracted {len(cleaned_text)} characters")
            return cleaned_text
            
        except pytesseract.TesseractError as e:
            error_msg = f"Tesseract OCR Error: {str(e)}"
            logger.error(error_msg)
            if "Unable to load language" in str(e):
                raise Exception(f"Language '{language}' is not installed. Please try English or check language settings.")
            else:
                raise Exception(f"OCR engine error: {str(e)}")
        except Exception as e:
            error_msg = f"OCR processing failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(f"Failed to process image: {str(e)}")
    
    @staticmethod
    def clean_extracted_text(text):
        """Clean and format the extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and clean up
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove lines that are too short (likely noise)
            stripped_line = line.strip()
            if len(stripped_line) > 1:  # Only keep lines with more than 1 character
                cleaned_lines.append(stripped_line)
        
        # Join lines with proper spacing
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Log the cleaned text for debugging
        if cleaned_text:
            logger.info(f"📝 Cleaned text preview: {cleaned_text[:100]}...")
        
        return cleaned_text
    
    @staticmethod
    def get_supported_languages():
        """Get list of supported languages"""
        try:
            # First ensure tesseract path is set
            ImageProcessor.setup_tesseract_path()
            
            # Get available languages from Tesseract
            available_langs = pytesseract.get_languages()
            logger.info(f"🌐 Available Tesseract languages: {available_langs}")
            
            # Map to our supported languages from config
            supported = {}
            for lang_name, lang_code in config.SUPPORTED_LANGUAGES.items():  # Use config.SUPPORTED_LANGUAGES directly
                if lang_code in available_langs:
                    supported[lang_name] = lang_code
            
            # If no languages found, return default English
            if not supported:
                supported['english'] = 'eng'
                
            logger.info(f"✅ Supported languages in bot: {list(supported.keys())}")
            return supported
        except Exception as e:
            logger.error(f"❌ Error getting supported languages: {e}")
            return {'english': 'eng'}

# Test Tesseract on import
print("🔍 Checking Tesseract installation...")
if ImageProcessor.check_tesseract_availability():
    print("✅ Tesseract OCR is properly configured!")
    print("📍 Path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
else:
    print("❌ Tesseract OCR configuration failed")