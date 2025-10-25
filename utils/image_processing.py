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
        """Optimize image for OCR while preserving text structure - FAST VERSION"""
        try:
            # Fast image loading
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale directly (faster than RGB conversion)
            if image.mode != 'L':
                image = image.convert('L')
            
            img_array = np.array(image)
            
            # Fast resizing - only if necessary
            height, width = img_array.shape
            if height > 1200 or width > 1200:  # Reduced from 1600
                scale = min(1200/height, 1200/width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_LINEAR)  # Faster than INTER_AREA
            
            # FAST preprocessing pipeline (skip heavy operations for local testing)
            # Only apply essential preprocessing
            if height * width > 500000:  # Only for large images
                # Simple contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))  # Reduced grid size
                img_array = clahe.apply(img_array)
            else:
                # For small images, just normalize
                img_array = cv2.normalize(img_array, None, 0, 255, cv2.NORM_MINMAX)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            # Ultra-fast fallback
            try:
                image = Image.open(io.BytesIO(image_bytes)).convert('L')
                return np.array(image)
            except Exception as fallback_error:
                logger.error(f"Fallback preprocessing also failed: {fallback_error}")
                # Create a simple black image as last resort
                return np.zeros((100, 100), dtype=np.uint8)

class ProductionOCRProcessor:
    """Production-grade OCR processor - OPTIMIZED FOR SPEED"""
    
    def __init__(self):
        self.preprocessor = AdvancedImagePreprocessor()
        self.executor = ThreadPoolExecutor(max_workers=2)  # Reduced workers
        
        # FAST configurations - simplified
        self.configs = {
            'fast': '--oem 1 --psm 6',  # Fastest engine, single text block
            'default': '--oem 1 --psm 6',
            'document': '--oem 1 --psm 3'
        }
        
        # Test Tesseract availability
        self._verify_tesseract()
    
    def _verify_tesseract(self):
        """Verify Tesseract is available and working"""
        try:
            # Get Tesseract version
            version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract version: {version}")
            
        except Exception as e:
            logger.error(f"❌ Tesseract verification failed: {e}")
            # Don't raise error, just log - we'll handle it in processing
    
    async def extract_text_optimized(self, image_bytes: bytes) -> str:
        """Main OCR extraction function - OPTIMIZED FOR SPEED"""
        start_time = time.time()
        
        try:
            # FAST preprocessing with timeout
            processed_img = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self.executor, self.preprocessor.preprocess_image, image_bytes
                ),
                timeout=5.0  # 5 second timeout for preprocessing
            )
            
            # FAST OCR extraction with reasonable timeout
            extracted_text = await asyncio.wait_for(
                self._extract_fast(processed_img),
                timeout=15.0  # 15 second timeout for OCR (reduced from 25)
            )
            
            processing_time = time.time() - start_time
            
            if extracted_text and len(extracted_text.strip()) > 2:  # Reduced from 5
                performance_monitor.record_request(processing_time)
                logger.info(f"✅ OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                performance_monitor.record_error()
                return "No readable text found in the image. Please try a clearer image with better lighting."
                
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            logger.warning(f"OCR processing timeout after {processing_time:.2f}s")
            performance_monitor.record_error()
            return "Processing took too long. Please try a smaller or simpler image."
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"OCR processing error after {processing_time:.2f}s: {e}")
            performance_monitor.record_error()
            return "Error processing image. Please try again with a different image."
    
    async def _extract_fast(self, image: np.ndarray) -> str:
        """FAST text extraction with minimal language attempts"""
        loop = asyncio.get_event_loop()
        config = self.configs['fast']
        
        # FAST language strategy - try only essential languages
        language_attempts = [
            'eng',    # Primary: English only (fastest)
        ]
        
        for lang in language_attempts:
            try:
                text = await loop.run_in_executor(
                    self.executor, self._extract_single_language_fast, image, lang, config
                )
                
                if text and len(text.strip()) > 1:
                    return text
                    
            except Exception as e:
                logger.debug(f"Language {lang} failed: {e}")
                continue
        
        # Final attempt: no language specified (fastest)
        try:
            text = await loop.run_in_executor(
                self.executor, pytesseract.image_to_string, image, config
            )
            return text.strip()
        except:
            return ""
    
    def _extract_single_language_fast(self, image: np.ndarray, lang: str, config: str) -> str:
        """FAST single language extraction"""
        try:
            # Use faster image_to_string instead of image_to_data
            text = pytesseract.image_to_string(image, lang=lang, config=config)
            return text.strip()
        except Exception as e:
            logger.debug(f"Fast OCR failed for {lang}: {e}")
            return ""

# Global instances
ocr_processor = ProductionOCRProcessor()
performance_monitor = PerformanceMonitor()