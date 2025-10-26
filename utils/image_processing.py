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
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# Configure Tesseract path for container environment
TESSERACT_CMD = '/usr/bin/tesseract'
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    logger.info(f"✅ Tesseract configured at: {TESSERACT_CMD}")

# Test OpenCV headless
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info(f"✅ OpenCV headless version: {cv2.__version__}")
except ImportError as e:
    logger.error(f"❌ OpenCV import failed: {e}")
    OPENCV_AVAILABLE = False

class PerformanceMonitor:
    """Performance monitoring for OCR operations"""
    def __init__(self):
        self.request_times = []
        self.success_count = 0
        self.error_count = 0
        self.last_confidence = 0
        
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
            "avg_confidence": self.last_confidence
        }

class AdvancedImagePreprocessor:
    """Advanced image preprocessing for optimal OCR results with OpenCV headless"""
    
    @staticmethod
    def preprocess_image(image_bytes: bytes) -> np.ndarray:
        """Optimize image for OCR while preserving text structure"""
        try:
            if not OPENCV_AVAILABLE:
                return AdvancedImagePreprocessor._preprocess_with_pil(image_bytes)
            
            # Convert bytes to numpy array using OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image with OpenCV")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Smart resizing - only if necessary
            height, width = gray.shape
            if height > 1600 or width > 1600:
                scale = min(1600/height, 1600/width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Enhanced preprocessing pipeline with OpenCV headless
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
            logger.error(f"OpenCV preprocessing error: {e}")
            # Fallback to PIL processing
            return AdvancedImagePreprocessor._preprocess_with_pil(image_bytes)
    
    @staticmethod
    def _preprocess_with_pil(image_bytes: bytes) -> np.ndarray:
        """Fallback preprocessing using PIL only"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if too large
            width, height = image.size
            if width > 1600 or height > 1600:
                scale = min(1600/width, 1600/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Convert to numpy array
            img_array = np.array(image)
            
            return img_array
            
        except Exception as e:
            logger.error(f"PIL preprocessing error: {e}")
            # Last resort fallback
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            return np.array(image)
    
    @staticmethod
    def detect_image_quality(image: np.ndarray) -> Dict[str, Any]:
        """Analyze image quality for optimal OCR configuration"""
        try:
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
        except Exception as e:
            logger.error(f"Image quality detection error: {e}")
            # Return default values
            return {
                "blur": 100,
                "contrast": 50,
                "brightness": 128,
                "is_blurry": False,
                "is_dark": False,
                "is_low_contrast": False
            }

class ProductionOCRProcessor:
    """Production-grade OCR processor with enhanced Amharic support"""
    
    def __init__(self):
        self.preprocessor = AdvancedImagePreprocessor()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Enhanced configurations using your language_support functions
        self.configs = {
            'paragraph': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'blurry': '--oem 3 --psm 6 -c textord_min_linesize=0.5',
            'default': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'amharic_optimized': '--oem 3 --psm 6 -c textord_min_linesize=1.8 -c preserve_interword_spaces=1 -c tessedit_do_invert=0'
        }
        
        logger.info("✅ Production OCR Processor initialized with enhanced Amharic support")
    
    async def extract_text_optimized(self, image_bytes: bytes) -> str:
        """Main OCR extraction function with enhanced language detection"""
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_img = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.preprocessor.preprocess_image, image_bytes
            )
            
            # Extract text with enhanced language detection
            extracted_text = await asyncio.wait_for(
                self._extract_with_smart_language_detection(processed_img),
                timeout=25.0
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
            return "Error processing image. Please try again with a different image."
    
    async def _extract_with_smart_language_detection(self, image: np.ndarray) -> str:
        """Smart OCR with language detection and optimized Amharic processing"""
        loop = asyncio.get_event_loop()
        
        # Strategy 1: Quick Amharic detection attempt
        quick_amharic_result = await self._quick_amharic_detection(image, loop)
        if quick_amharic_result:
            return quick_amharic_result
        
        # Strategy 2: Multi-language approach with confidence scoring
        multi_lang_result = await self._multi_language_approach(image, loop)
        if multi_lang_result:
            return multi_lang_result
        
        # Strategy 3: Final fallback attempts
        return await self._final_fallback_attempts(image, loop)
    
    async def _quick_amharic_detection(self, image: np.ndarray, loop) -> str:
        """Quick attempt to detect and extract Amharic text"""
        try:
            # First, try Amharic-only with optimized settings
            amh_text = await loop.run_in_executor(
                self.executor, 
                pytesseract.image_to_string, 
                image, 'amh', self.configs['amharic_optimized']
            )
            
            if amh_text and self._validate_amharic_extraction(amh_text):
                logger.info("✅ Quick Amharic detection successful")
                return amh_text.strip()
                
        except Exception as e:
            logger.debug(f"Quick Amharic detection failed: {e}")
        
        return ""
    
    async def _multi_language_approach(self, image: np.ndarray, loop) -> str:
        """Multi-language OCR with confidence-based selection"""
        language_attempts = [
            # Priority: Amharic-focused attempts
            ('amh+eng', self.configs['amharic_optimized'], 'Amharic+English'),
            ('eng+amh', self.configs['paragraph'], 'English+Amharic'),
            ('amh', self.configs['amharic_optimized'], 'Amharic only'),
            
            # Fallback: English and other combinations
            ('eng', self.configs['paragraph'], 'English only'),
            ('', self.configs['paragraph'], 'Auto-detect'),
        ]
        
        best_result = {"text": "", "confidence": 0, "language": "unknown"}
        
        for lang, config, attempt_name in language_attempts:
            try:
                text = await loop.run_in_executor(
                    self.executor, 
                    self._extract_with_confidence, 
                    image, lang, config
                )
                
                if text and len(text.strip()) > 5:
                    # Calculate confidence score
                    confidence = self._calculate_extraction_confidence(text, lang)
                    
                    logger.info(f"📊 {attempt_name}: {len(text.strip())} chars, confidence: {confidence:.2f}")
                    
                    # Update best result if this is better
                    if confidence > best_result["confidence"]:
                        best_result = {
                            "text": text.strip(),
                            "confidence": confidence,
                            "language": lang
                        }
                        
                    # Early exit for high-confidence Amharic
                    if 'amh' in lang and confidence > 0.7:
                        logger.info(f"🚀 High-confidence {attempt_name} result, stopping early")
                        break
                        
            except Exception as e:
                logger.debug(f"Attempt {attempt_name} failed: {e}")
                continue
        
        return best_result["text"] if best_result["text"] else ""
    
    async def _final_fallback_attempts(self, image: np.ndarray, loop) -> str:
        """Final fallback attempts when other methods fail"""
        fallback_attempts = [
            ('eng', self.configs['paragraph']),
            ('', self.configs['paragraph']),  # No language specified
        ]
        
        for lang, config in fallback_attempts:
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, config
                )
                if text and len(text.strip()) > 2:
                    return text.strip()
            except Exception as e:
                logger.debug(f"Fallback {lang} failed: {e}")
                continue
        
        return ""
    
    def _extract_with_confidence(self, image: np.ndarray, lang: str, config: str) -> str:
        """Extract text and calculate confidence"""
        try:
            # Use image_to_data to get confidence information
            data = pytesseract.image_to_data(
                image, 
                lang=lang, 
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Reconstruct text
            text = self._reconstruct_paragraphs(data)
            
            # Calculate average confidence
            if len(data['conf']) > 0:
                valid_confidences = [conf for conf in data['conf'] if conf > 0]
                if valid_confidences:
                    avg_confidence = sum(valid_confidences) / len(valid_confidences)
                    performance_monitor.last_confidence = avg_confidence
            
            return text if text else pytesseract.image_to_string(image, lang=lang, config=config).strip()
            
        except Exception as e:
            logger.debug(f"Confidence extraction failed for {lang}: {e}")
            # Fallback to simple extraction
            return pytesseract.image_to_string(image, lang=lang, config=config).strip()
    
    def _calculate_extraction_confidence(self, text: str, lang_used: str) -> float:
        """Calculate confidence score for extracted text"""
        if not text:
            return 0.0
        
        base_confidence = 0.5
        
        # Length factor
        length_factor = min(len(text.strip()) / 100, 1.0)  # Max 1.0 for 100+ chars
        
        # Language-specific validation
        if 'amh' in lang_used:
            from ocr_engine.language_support import validate_amharic_text
            if validate_amharic_text(text):
                base_confidence += 0.3
        else:
            from ocr_engine.language_support import validate_english_text
            if validate_english_text(text):
                base_confidence += 0.3
        
        # Character diversity factor
        unique_chars = len(set(text))
        diversity_factor = min(unique_chars / 10, 0.2)  # Max 0.2 for 10+ unique chars
        
        return min(base_confidence + length_factor + diversity_factor, 1.0)
    
    def _validate_amharic_extraction(self, text: str) -> bool:
        """Validate if extracted text contains meaningful Amharic content"""
        from ocr_engine.language_support import validate_amharic_text, is_amharic_character
        
        if not text or len(text.strip()) < 5:
            return False
        
        # Use your existing validation function
        if validate_amharic_text(text):
            return True
        
        # Additional check: ensure we have some Amharic characters
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        return amharic_chars >= 3  # At least 3 Amharic characters
    
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

# Global instances (same as your original)
ocr_processor = ProductionOCRProcessor()
performance_monitor = PerformanceMonitor()