# utils/image_processing.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Dict, Any
import io
from PIL import Image
import re

logger = logging.getLogger(__name__)

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
            return {"avg_time": 0, "success_rate": 0}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "avg_time": avg_time,
            "success_rate": success_rate,
            "total_requests": total_requests
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
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return np.array(image)
    
    @staticmethod
    def detect_image_quality(image: np.ndarray) -> Dict[str, Any]:
        """Analyze image quality for optimal OCR configuration"""
        # Blur detection
        blur_value = cv2.Laplacian(image, cv2.CV_64F).var()
        
        # Contrast and brightness
        contrast = image.std()
        brightness = image.mean()
        
        return {
            "blur": blur_value,
            "contrast": contrast,
            "brightness": brightness,
            "is_blurry": blur_value < 50,
            "is_dark": brightness < 80,
            "is_low_contrast": contrast < 40
        }

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
        
        self.languages = ['eng', 'amh', 'eng+amh', 'chi_sim+eng']
    
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
                self._extract_with_paragraphs(processed_img, config_type),
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
            return "⏱️ Processing took too long. Please try a smaller image (under 2MB)."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    def _select_optimal_config(self, quality_info: Dict) -> str:
        """Select optimal OCR configuration based on image analysis"""
        if quality_info['is_blurry']:
            return 'blurry'
        elif quality_info['is_low_contrast']:
            return 'blurry'
        else:
            return 'paragraph'
    
    async def _extract_with_paragraphs(self, image: np.ndarray, config_type: str) -> str:
        """Extract text with intelligent paragraph detection"""
        loop = asyncio.get_event_loop()
        
        config = self.configs[config_type]
        best_text = ""
        
        # Try languages in order of priority
        for lang in self.languages:
            try:
                text = await loop.run_in_executor(
                    self.executor, self._extract_paragraph_text, image, lang, config
                )
                
                if text and len(text.strip()) > len(best_text.strip()):
                    best_text = text
                    # Early exit if we get good results with primary language
                    if lang == 'eng' and len(text.strip()) > 20:
                        break
                        
            except Exception as e:
                logger.debug(f"Language {lang} failed: {e}")
                continue
        
        return best_text
    
    def _extract_paragraph_text(self, image: np.ndarray, lang: str, config: str) -> str:
        """Extract text with paragraph structure preservation"""
        try:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                image, 
                lang=lang, 
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Reconstruct text with paragraph detection
            paragraph_text = self._reconstruct_paragraphs(data)
            
            return paragraph_text
            
        except Exception as e:
            logger.debug(f"Paragraph extraction failed for {lang}: {e}")
            # Fallback to simple extraction
            return pytesseract.image_to_string(image, lang=lang, config=config).strip()
    
    def _reconstruct_paragraphs(self, data: Dict) -> str:
        """Intelligent paragraph reconstruction from OCR data"""
        paragraphs = []
        current_paragraph = []
        current_block = -1
        previous_bottom = 0
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            block_num = data['block_num'][i]
            top = data['top'][i]
            height = data['height'][i]
            
            if text and confidence > 20:  # Use confident detections
                current_bottom = top + height
                
                # Paragraph detection logic:
                # - New block number indicates new paragraph
                # - Large vertical gap indicates new paragraph
                is_new_paragraph = (
                    block_num != current_block or
                    (previous_bottom > 0 and top - previous_bottom > height * 1.5)
                )
                
                if is_new_paragraph and current_paragraph:
                    # Finalize current paragraph
                    paragraph_text = ' '.join(current_paragraph)
                    if paragraph_text.strip():
                        paragraphs.append(paragraph_text)
                    current_paragraph = []
                
                current_paragraph.append(text)
                current_block = block_num
                previous_bottom = current_bottom
        
        # Add the final paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            if paragraph_text.strip():
                paragraphs.append(paragraph_text)
        
        # Join paragraphs with proper spacing
        if paragraphs:
            return '\n\n'.join(paragraphs)
        else:
            # Fallback to line-by-line extraction
            return self._fallback_line_extraction(data)
    
    def _fallback_line_extraction(self, data: Dict) -> str:
        """Fallback method for line-by-line text extraction"""
        lines = []
        current_line = []
        last_top = None
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            top = data['top'][i]
            
            if text and conf > 20:
                # Detect line breaks based on vertical position
                if last_top is not None and abs(top - last_top) > 10:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = []
                
                current_line.append(text)
                last_top = top
        
        # Add the final line
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
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