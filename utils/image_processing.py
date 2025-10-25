# utils/image_processing.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Dict, Any
import io
from PIL import Image
import re

logger = logging.getLogger(__name__)

# Configure Tesseract path for container environment
TESSERACT_CMD = '/usr/bin/tesseract'
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    logger.info(f"✅ Tesseract configured at: {TESSERACT_CMD}")
else:
    # Fallback to system PATH
    logger.info("ℹ️ Using Tesseract from system PATH")

class PerformanceMonitor:
    """Performance monitoring for OCR operations"""
    def __init__(self):
        self.request_times = []
        self.success_count = 0
        self.error_count = 0
        
    def record_request(self, processing_time: float):
        self.request_times.append(processing_time)
        self.success_count += 1
        if len(self.request_times) > 100:
            self.request_times.pop(0)
            
    def record_error(self):
        self.error_count += 1
        
    def get_stats(self):
        if not self.request_times:
            return {"avg_time": 0, "success_rate": 0, "avg_confidence": 85.0}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "avg_time": avg_time,
            "success_rate": success_rate,
            "total_requests": total_requests,
            "avg_confidence": 85.0  # Default confidence
        }

class AdvancedImagePreprocessor:
    """Advanced image preprocessing for optimal OCR results"""
    
    @staticmethod
    def preprocess_image(image_bytes: bytes) -> np.ndarray:
        """Optimize image for OCR while preserving text structure"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image.convert('RGB'))
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Smart resizing - only if necessary
            height, width = gray.shape
            if height > 1600 or width > 1600:
                scale = min(1600/height, 1600/width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Enhanced preprocessing pipeline
            # Step 1: Denoising
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            
            # Step 2: Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Step 3: Light sharpening for blurry text
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            return sharpened
            
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            # Fallback to simple conversion
            try:
                image = Image.open(io.BytesIO(image_bytes)).convert('L')
                return np.array(image)
            except Exception as fallback_error:
                logger.error(f"Fallback preprocessing also failed: {fallback_error}")
                raise

class ProductionOCRProcessor:
    """Production-grade OCR processor with paragraph detection"""
    
    def __init__(self):
        self.preprocessor = AdvancedImagePreprocessor()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Optimized configurations
        self.configs = {
            'paragraph': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'blurry': '--oem 3 --psm 6 -c textord_min_linesize=0.5',
            'default': '--oem 3 --psm 6 -c preserve_interword_spaces=1'
        }
        
        # Test Tesseract availability
        self._verify_tesseract()
    
    def _verify_tesseract(self):
        """Verify Tesseract is available and working"""
        try:
            # Get Tesseract version
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract version: {version}")
            
            # List available languages
            try:
                langs = pytesseract.get_languages()
                logger.info(f"✅ Available languages: {langs}")
            except:
                logger.info("ℹ️ Could not list languages, but Tesseract is available")
                
        except Exception as e:
            logger.error(f"❌ Tesseract verification failed: {e}")
            raise RuntimeError("OCR system is currently unavailable. Please try again later.")
    
    async def extract_text_optimized(self, image_bytes: bytes) -> str:
        """Main OCR extraction function with timeout protection"""
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_img = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.preprocessor.preprocess_image, image_bytes
            )
            
            # Analyze image for optimal configuration
            quality_info = self.preprocessor.detect_image_quality(processed_img)
            config_type = self._select_optimal_config(quality_info)
            
            # Extract text with paragraph detection
            extracted_text = await asyncio.wait_for(
                self._extract_with_fallback(processed_img, config_type),
                timeout=25.0  # 25 second timeout
            )
            
            processing_time = time.time() - start_time
            
            if extracted_text and len(extracted_text.strip()) > 5:
                performance_monitor.record_request(processing_time)
                logger.info(f"✅ Production OCR completed in {processing_time:.2f}s")
                return extracted_text
            else:
                performance_monitor.record_error()
                return self._get_error_message()
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            performance_monitor.record_error()
            return "⏱️ Processing took too long. Please try a smaller image (under 2MB)."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            performance_monitor.record_error()
            return "❌ OCR system is currently unavailable. Please try again later."
    
    def _select_optimal_config(self, quality_info: Dict) -> str:
        """Select optimal OCR configuration based on image analysis"""
        if quality_info.get('is_blurry', False):
            return 'blurry'
        elif quality_info.get('is_low_contrast', False):
            return 'blurry'
        else:
            return 'paragraph'
    
    async def _extract_with_fallback(self, image: np.ndarray, config_type: str) -> str:
        """Extract text with intelligent fallback strategy"""
        loop = asyncio.get_event_loop()
        config = self.configs[config_type]
        
        # Language fallback strategy
        language_attempts = [
            'eng',  # Primary: English
            'eng+amh',  # Secondary: English + Amharic
            'amh',  # Tertiary: Amharic only
        ]
        
        best_text = ""
        
        for lang in language_attempts:
            try:
                logger.info(f"Attempting OCR with language: {lang}")
                text = await loop.run_in_executor(
                    self.executor, self._extract_single_language, image, lang, config
                )
                
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
                    logger.info(f"✅ Got better results with {lang}: {len(text)} chars")
                    
                    # Early exit if we get good results
                    if len(text.strip()) > 20:
                        break
                        
            except Exception as e:
                logger.debug(f"Language {lang} failed: {e}")
                continue
        
        return best_text if best_text.strip() else await self._extract_any_language(image, config)
    
    def _extract_single_language(self, image: np.ndarray, lang: str, config: str) -> str:
        """Extract text with a single language"""
        try:
            return pytesseract.image_to_string(image, lang=lang, config=config).strip()
        except Exception as e:
            logger.warning(f"OCR failed for {lang}: {e}")
            return ""
    
    async def _extract_any_language(self, image: np.ndarray, config: str) -> str:
        """Final fallback: try OCR without specifying language"""
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                self.executor, pytesseract.image_to_string, image, config
            )
            return text.strip()
        except Exception as e:
            logger.error(f"Final OCR fallback failed: {e}")
            return ""
    
    def _get_error_message(self) -> str:
        """Get user-friendly error message"""
        return (
            "❌ No readable text found.\n\n"
            "💡 *Tips for better results:*\n"
            "• Use clear, high-contrast images\n"
            "• Ensure text is horizontal and focused\n"
            "• Good lighting reduces errors\n"
            "• Avoid blurry or distorted text\n\n"
            "📸 *Ideal images:*\n"
            "• Documents and printed text\n"
            "• High-quality screenshots\n"
            "• Well-lit photos of text\n"
            "• Images under 5MB in size"
        )

# Global instances
ocr_processor = ProductionOCRProcessor()
performance_monitor = PerformanceMonitor()