# utils/smart_ocr.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple
import io
from PIL import Image, ImageEnhance, ImageFilter
import re

logger = logging.getLogger(__name__)

class SmartOCRProcessor:
    """Smart OCR processor with enhanced blurry/low-visibility text detection"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.setup_ocr_configs()
        
    def setup_ocr_configs(self):
        """Optimized OCR configurations for various image qualities"""
        self.configs = {
            # Standard configurations
            'english_standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'amharic_standard': '--oem 3 --psm 6 -c textord_min_linesize=1.8 -c preserve_interword_spaces=1',
            'auto': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7 -c preserve_interword_spaces=1',
            # Enhanced for blurry/low-quality images
            'blurry_english': '--oem 3 --psm 6 -c textord_min_linesize=0.5 -c textord_old_baselines=1',
            'blurry_amharic': '--oem 3 --psm 6 -c textord_min_linesize=0.8 -c textord_old_baselines=1',
            'low_contrast': '--oem 3 --psm 6 -c tessedit_do_invert=1 -c textord_min_linesize=0.5'
        }
        
        logger.info("✅ Smart OCR Processor initialized with enhanced blurry text detection")
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """Enhanced OCR extraction optimized for blurry/low-visibility images"""
        start_time = time.time()
        
        try:
            # Enhanced preprocessing for blurry images
            processed_img, image_quality = await asyncio.wait_for(
                self._enhanced_preprocess(image_bytes),
                timeout=5.0
            )
            
            logger.info(f"🔍 Image quality: {image_quality['quality']} (blurry: {image_quality['is_blurry']}, low_contrast: {image_quality['is_low_contrast']})")
            
            # Extract with quality-optimized approach
            extracted_text = await asyncio.wait_for(
                self._quality_optimized_extraction(processed_img, image_quality),
                timeout=15.0
            )
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_reasonable_text(extracted_text):
                logger.info(f"✅ OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                # Enhanced fallback for difficult images
                final_text = await self._enhanced_fallback(processed_img, image_quality)
                if final_text and self._is_reasonable_text(final_text):
                    logger.info(f"✅ Enhanced fallback completed in {processing_time:.2f}s")
                    return final_text
                else:
                    logger.warning("❌ No reasonable text extracted after enhanced attempts")
                    return "No readable text found. The image might be too blurry, low contrast, or contain no visible text."
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _enhanced_preprocess(self, image_bytes: bytes) -> tuple:
        """Enhanced preprocessing optimized for blurry and low-visibility images"""
        try:
            # Convert to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Analyze image quality
            quality_info = self._analyze_image_quality(gray)
            
            # Apply quality-specific preprocessing
            if quality_info['is_blurry']:
                processed = self._enhance_blurry_image(gray)
            elif quality_info['is_low_contrast']:
                processed = self._enhance_low_contrast_image(gray)
            elif quality_info['is_dark']:
                processed = self._enhance_dark_image(gray)
            else:
                processed = self._standard_enhancement(gray)
            
            return processed, quality_info
            
        except Exception as e:
            logger.error(f"Enhanced preprocessing failed: {e}")
            # Fallback to simple processing with default quality info
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            img_array = np.array(image)
            quality_info = self._analyze_image_quality(img_array)
            return img_array, quality_info
    
    def _analyze_image_quality(self, image: np.ndarray) -> Dict:
        """Comprehensive image quality analysis"""
        # Blur detection using Laplacian variance
        blur_value = cv2.Laplacian(image, cv2.CV_64F).var()
        
        # Contrast and brightness analysis
        contrast = image.std()
        brightness = image.mean()
        
        # Additional quality metrics
        min_val, max_val = image.min(), image.max()
        dynamic_range = max_val - min_val
        
        return {
            "blur": blur_value,
            "contrast": contrast,
            "brightness": brightness,
            "dynamic_range": dynamic_range,
            "is_blurry": blur_value < 30,  # Lower threshold for blur detection
            "is_low_contrast": contrast < 25 or dynamic_range < 50,
            "is_dark": brightness < 60,
            "quality": "good" if blur_value > 50 and contrast > 40 else "poor"
        }
    
    def _enhance_blurry_image(self, image: np.ndarray) -> np.ndarray:
        """Specialized enhancement for blurry images"""
        try:
            # Step 1: Strong noise reduction
            denoised = cv2.medianBlur(image, 3)
            
            # Step 2: Aggressive sharpening for blurry text
            kernel = np.array([[-1, -1, -1, -1, -1],
                              [-1,  2,  2,  2, -1],
                              [-1,  2,  8,  2, -1],
                              [-1,  2,  2,  2, -1],
                              [-1, -1, -1, -1, -1]]) / 8.0
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            # Step 3: High contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
            high_contrast = clahe.apply(sharpened)
            
            # Step 4: Bilateral filter to preserve edges while reducing noise
            bilateral = cv2.bilateralFilter(high_contrast, 9, 75, 75)
            
            return bilateral
            
        except Exception as e:
            logger.error(f"Blurry enhancement failed: {e}")
            return image
    
    def _enhance_low_contrast_image(self, image: np.ndarray) -> np.ndarray:
        """Specialized enhancement for low-contrast images"""
        try:
            # Step 1: Histogram equalization for global contrast
            equalized = cv2.equalizeHist(image)
            
            # Step 2: Adaptive histogram equalization for local contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            adaptive = clahe.apply(equalized)
            
            # Step 3: Gamma correction for brightness adjustment
            gamma = 1.5
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gamma_corrected = cv2.LUT(adaptive, table)
            
            return gamma_corrected
            
        except Exception as e:
            logger.error(f"Low contrast enhancement failed: {e}")
            return image
    
    def _enhance_dark_image(self, image: np.ndarray) -> np.ndarray:
        """Specialized enhancement for dark images"""
        try:
            # Step 1: Brightness adjustment
            brightened = cv2.convertScaleAbs(image, alpha=1.5, beta=50)
            
            # Step 2: Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            contrasted = clahe.apply(brightened)
            
            # Step 3: Reduce noise while preserving edges
            denoised = cv2.fastNlMeansDenoising(contrasted, h=20)
            
            return denoised
            
        except Exception as e:
            logger.error(f"Dark image enhancement failed: {e}")
            return image
    
    def _standard_enhancement(self, image: np.ndarray) -> np.ndarray:
        """Standard enhancement for good quality images"""
        try:
            # Basic denoising
            denoised = cv2.fastNlMeansDenoising(image, h=10)
            
            # Moderate contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Light sharpening
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            return sharpened
            
        except Exception as e:
            logger.error(f"Standard enhancement failed: {e}")
            return image
    
    async def _quality_optimized_extraction(self, image: np.ndarray, quality_info: Dict) -> str:
        """Extraction optimized for image quality"""
        loop = asyncio.get_event_loop()
        
        # Choose strategies based on image quality
        if quality_info['is_blurry']:
            strategies = self._get_blurry_strategies()
        elif quality_info['is_low_contrast']:
            strategies = self._get_low_contrast_strategies()
        else:
            strategies = self._get_standard_strategies()
        
        for lang, config, strategy_name in strategies:
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, self.configs[config]
                )
                
                if text and len(text.strip()) > 2:
                    logger.info(f"📊 {strategy_name}: {len(text.strip())} chars")
                    
                    if self._is_reasonable_text(text):
                        return text.strip()
                        
            except Exception as e:
                logger.debug(f"Strategy {strategy_name} failed: {e}")
                continue
        
        return ""
    
    def _get_blurry_strategies(self) -> List[Tuple]:
        """Strategies for blurry images"""
        return [
            ('eng', 'blurry_english', 'Blurry English'),
            ('amh', 'blurry_amharic', 'Blurry Amharic'),
            ('eng+amh', 'blurry_english', 'Blurry Combined'),
            ('eng', 'single_line', 'Blurry Single Line English'),
            ('amh', 'single_line', 'Blurry Single Line Amharic'),
        ]
    
    def _get_low_contrast_strategies(self) -> List[Tuple]:
        """Strategies for low-contrast images"""
        return [
            ('eng', 'low_contrast', 'Low Contrast English'),
            ('amh', 'low_contrast', 'Low Contrast Amharic'),
            ('eng', 'blurry_english', 'Low Contrast Fallback English'),
            ('amh', 'blurry_amharic', 'Low Contrast Fallback Amharic'),
        ]
    
    def _get_standard_strategies(self) -> List[Tuple]:
        """Standard strategies for good quality images"""
        return [
            ('eng', 'english_standard', 'English Standard'),
            ('amh', 'amharic_standard', 'Amharic Standard'),
            ('eng+amh', 'auto', 'Combined'),
            ('eng', 'document', 'English Document'),
            ('amh', 'document', 'Amharic Document'),
        ]
    
    async def _enhanced_fallback(self, image: np.ndarray, quality_info: Dict) -> str:
        """Enhanced fallback for difficult images"""
        loop = asyncio.get_event_loop()
        
        # Try multiple preprocessing variations for difficult images
        preprocessing_variations = [
            self._apply_aggressive_enhancement,
            self._apply_inversion,
            self._apply_thresholding,
        ]
        
        for preprocess_func in preprocessing_variations:
            try:
                enhanced_img = preprocess_func(image)
                
                # Try extraction on enhanced image
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    enhanced_img, 'eng+amh', self.configs['auto']
                )
                
                if text and len(text.strip()) > 2 and self._is_reasonable_text(text):
                    logger.info(f"🔄 Enhanced fallback succeeded: {len(text.strip())} chars")
                    return text.strip()
                    
            except Exception as e:
                logger.debug(f"Enhanced fallback variation failed: {e}")
                continue
        
        return ""
    
    def _apply_aggressive_enhancement(self, image: np.ndarray) -> np.ndarray:
        """Apply aggressive enhancement for very difficult images"""
        # High-pass filter for edge enhancement
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        filtered = cv2.filter2D(image, -1, kernel)
        
        # Extreme contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(4, 4))
        contrasted = clahe.apply(filtered)
        
        return contrasted
    
    def _apply_inversion(self, image: np.ndarray) -> np.ndarray:
        """Apply image inversion (white text on black background)"""
        return cv2.bitwise_not(image)
    
    def _apply_thresholding(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding"""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
    
    def _is_reasonable_text(self, text: str) -> bool:
        """Check if text is reasonable (more permissive for difficult images)"""
        if not text or len(text.strip()) < 2:  # Lower threshold
            return False
        
        clean_text = text.strip()
        
        # More permissive validation for difficult images
        if len(clean_text) < 2:
            return False
        
        # Check character diversity (more permissive)
        unique_chars = len(set(clean_text))
        if unique_chars < 1:
            return False
        
        # Less strict garbage detection for difficult images
        if self._is_obvious_garbage(text):
            return False
        
        return True
    
    def _is_obvious_garbage(self, text: str) -> bool:
        """Detect obvious garbage text (more permissive)"""
        if not text:
            return True
        
        # More permissive special character ratio for difficult images
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars / len(text) > 0.7:  # Higher threshold
            return True
        
        # Repeated nonsense patterns
        nonsense_patterns = [
            r'(.)\1{8,}',  # Same character repeated 9+ times
        ]
        
        for pattern in nonsense_patterns:
            if re.search(pattern, text):
                return True
        
        return False

# Global instance
smart_ocr_processor = SmartOCRProcessor()