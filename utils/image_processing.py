# utils/image_processing.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional, Dict, Any
import io
from PIL import Image, ImageEnhance, ImageFilter
import re

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Enhanced performance monitoring"""
    def __init__(self):
        self.request_times = []
        self.success_count = 0
        self.error_count = 0
        self.engine_stats = {}
        
    def record_request(self, processing_time: float, engine_used: str = "tesseract"):
        self.request_times.append(processing_time)
        self.success_count += 1
        self.engine_stats[engine_used] = self.engine_stats.get(engine_used, 0) + 1
        
        if len(self.request_times) > 100:
            self.request_times.pop(0)
            
    def record_error(self, engine: str = "tesseract"):
        self.error_count += 1
        self.engine_stats[engine] = self.engine_stats.get(engine, 0) + 1
        
    def get_stats(self):
        if not self.request_times:
            return {"avg_time": 0, "success_rate": 0}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "avg_time": avg_time,
            "success_rate": success_rate,
            "total_requests": total_requests,
            "engine_stats": self.engine_stats
        }

class AdvancedImagePreprocessor:
    """Advanced image preprocessing with multiple enhancement strategies"""
    
    @staticmethod
    def enhance_image_quality(image: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """Generate multiple enhanced versions of the image"""
        enhanced_versions = []
        
        # Original grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        enhanced_versions.append(('original', gray))
        
        # Strategy 1: CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        clahe_img = clahe.apply(gray)
        enhanced_versions.append(('clahe', clahe_img))
        
        # Strategy 2: Denoising + Sharpening for blurry images
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        enhanced_versions.append(('sharpened', sharpened))
        
        # Strategy 3: Bilateral filter for noise reduction while preserving edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        enhanced_versions.append(('bilateral', bilateral))
        
        # Strategy 4: Morphological operations for text cleaning
        kernel = np.ones((2,2), np.uint8)
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        enhanced_versions.append(('morphological', morph))
        
        return enhanced_versions
    
    @staticmethod
    def binarize_images(enhanced_versions: List[Tuple[str, np.ndarray]]) -> List[Tuple[str, np.ndarray]]:
        """Apply multiple binarization strategies"""
        binarized_versions = []
        
        for name, img in enhanced_versions:
            # Adaptive Gaussian threshold
            adaptive_gauss = cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            binarized_versions.append((f"{name}_adaptive_gauss", adaptive_gauss))
            
            # Adaptive Mean threshold
            adaptive_mean = cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            binarized_versions.append((f"{name}_adaptive_mean", adaptive_mean))
            
            # Otsu's threshold
            _, otsu = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            binarized_versions.append((f"{name}_otsu", otsu))
        
        return binarized_versions
    
    @staticmethod
    def resize_for_optimal_ocr(img: np.ndarray) -> np.ndarray:
        """Resize image for optimal OCR performance"""
        height, width = img.shape
        
        # Don't resize if already optimal (300-2000 pixels)
        if 300 <= height <= 2000 and 300 <= width <= 2000:
            return img
        
        # Calculate optimal size maintaining aspect ratio
        scale = 1.0
        if height < 300:
            scale = max(scale, 300 / height)
        if width < 300:
            scale = max(scale, 300 / width)
        if height > 2000:
            scale = min(scale, 2000 / height)
        if width > 2000:
            scale = min(scale, 2000 / width)
        
        if scale != 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return img
    
    @staticmethod
    def detect_image_characteristics(img: np.ndarray) -> Dict[str, Any]:
        """Comprehensive image quality analysis"""
        # Blur detection
        blur_value = cv2.Laplacian(img, cv2.CV_64F).var()
        
        # Contrast and brightness
        contrast = img.std()
        brightness = img.mean()
        
        # Text density estimation
        edges = cv2.Canny(img, 50, 150)
        text_density = np.sum(edges > 0) / (img.shape[0] * img.shape[1])
        
        # Noise level
        noise_level = cv2.mean(cv2.medianBlur(img, 3) - img)[0]
        
        return {
            "blur": blur_value,
            "contrast": contrast,
            "brightness": brightness,
            "text_density": text_density,
            "noise_level": abs(noise_level),
            "resolution": f"{img.shape[1]}x{img.shape[0]}",
            "is_blurry": blur_value < 50,
            "is_dark": brightness < 80,
            "is_low_contrast": contrast < 40
        }

class TesseractOptimizer:
    """Optimized Tesseract configurations for different scenarios"""
    
    def __init__(self):
        self.configs = self._build_configurations()
        self.language_combinations = self._build_language_combinations()
    
    def _build_configurations(self) -> Dict[str, str]:
        """Build comprehensive Tesseract configurations"""
        base_config = "--oem 3 -c tessedit_do_invert=0"
        
        return {
            # PSM 6: Uniform block of text (default)
            'default': f"{base_config} --psm 6 -c preserve_interword_spaces=1",
            
            # PSM 4: Single column of text
            'single_column': f"{base_config} --psm 4 -c preserve_interword_spaces=1",
            
            # PSM 3: Fully automatic page segmentation
            'auto_page': f"{base_config} --psm 3 -c preserve_interword_spaces=1",
            
            # PSM 7: Single text line
            'single_line': f"{base_config} --psm 7 -c preserve_interword_spaces=1",
            
            # PSM 8: Single word
            'single_word': f"{base_config} --psm 8 -c preserve_interword_spaces=1",
            
            # PSM 13: Raw line without specific processing
            'raw_line': f"{base_config} --psm 13",
            
            # Blurry image optimizations
            'blurry': f"{base_config} --psm 6 -c textord_min_linesize=0.3 -c textord_old_baselines=1 -c textord_noise_rej=0",
            
            # Small text optimizations
            'small_text': f"{base_config} --psm 6 -c textord_min_linesize=0.5 -c tessedit_char_blacklist=.,|[](){{}}",
            
            # Document optimizations
            'document': f"{base_config} --psm 3 -c preserve_interword_spaces=1 -c textord_heavy_nr=1",
            
            # Sparse text
            'sparse': f"{base_config} --psm 11 -c preserve_interword_spaces=1",
            
            # CJK characters optimization
            'cjk': f"{base_config} --psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=0",
            
            # Arabic script optimization
            'arabic': f"{base_config} --psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=1 -c textord_old_baselines=1",
            
            # Paragraph-optimized configuration
            'paragraph': f"{base_config} --psm 6 -c preserve_interword_spaces=1 -c textord_min_linesize=1.0 -c textord_tabfind_vertical_text=0 -c textord_really_old_xheight=1"
        }
    
    def _build_language_combinations(self) -> List[Tuple[str, str]]:
        """Build optimized language combinations"""
        return [
            ('eng', 'English'),
            ('amh', 'Amharic'),
            ('eng+amh', 'English+Amharic'),
            ('chi_sim', 'Chinese Simplified'),
            ('chi_sim+eng', 'Chinese+English'),
            ('jpn', 'Japanese'),
            ('jpn+eng', 'Japanese+English'),
            ('kor', 'Korean'),
            ('kor+eng', 'Korean+English'),
            ('ara', 'Arabic'),
            ('ara+eng', 'Arabic+English'),
            ('rus', 'Russian'),
            ('rus+eng', 'Russian+English'),
            ('spa', 'Spanish'),
            ('spa+eng', 'Spanish+English'),
            ('fra', 'French'),
            ('fra+eng', 'French+English'),
            ('deu', 'German'),
            ('deu+eng', 'German+English'),
            ('multiple', 'eng+spa+fra+deu+rus'),
        ]
    
    def get_optimal_configs(self, image_characteristics: Dict) -> List[Tuple[str, str, str]]:
        """Select optimal configurations based on image analysis"""
        configs_to_try = []
        
        # Always include paragraph-optimized config first
        configs_to_try.extend([
            ('paragraph', 'eng', 'Paragraph English'),
            ('paragraph', 'eng+amh', 'Paragraph English+Amharic'),
        ])
        
        # Base on blurriness
        if image_characteristics['is_blurry']:
            configs_to_try.extend([
                ('blurry', 'eng', 'Blurry English'),
                ('blurry', 'eng+amh', 'Blurry English+Amharic'),
                ('small_text', 'eng', 'Small Text English'),
            ])
        
        # Based on text density
        if image_characteristics['text_density'] > 0.1:
            configs_to_try.extend([
                ('document', 'eng', 'Document English'),
                ('default', 'eng+amh', 'Dense Text English+Amharic'),
            ])
        else:
            configs_to_try.extend([
                ('sparse', 'eng', 'Sparse Text English'),
                ('single_column', 'eng', 'Sparse Column English'),
            ])
        
        # Based on contrast
        if image_characteristics['is_low_contrast']:
            configs_to_try.extend([
                ('blurry', 'eng', 'Low Contrast English'),
                ('small_text', 'eng', 'Low Contrast Small Text'),
            ])
        
        # Always include default configurations
        configs_to_try.extend([
            ('default', 'eng', 'Default English'),
            ('default', 'eng+amh', 'Default English+Amharic'),
            ('auto_page', 'multiple', 'Auto Page Multiple'),
        ])
        
        # Remove duplicates and limit to 6 configurations for performance
        unique_configs = list(dict.fromkeys(configs_to_try))
        return unique_configs[:8]

class AdvancedParagraphOCR:
    """Advanced OCR with intelligent paragraph detection"""
    
    def __init__(self):
        self.preprocessor = AdvancedImagePreprocessor()
        self.optimizer = TesseractOptimizer()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    async def extract_text_optimized(self, image_bytes: bytes) -> str:
        """Advanced text extraction with intelligent paragraph detection"""
        start_time = time.time()
        
        try:
            # Convert bytes to numpy array
            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image.convert('RGB'))
            
            # Resize for optimal processing
            img_array = self.preprocessor.resize_for_optimal_ocr(
                cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            )
            
            # Analyze image characteristics
            characteristics = self.preprocessor.detect_image_characteristics(img_array)
            
            # Generate enhanced versions
            enhanced_versions = self.preprocessor.enhance_image_quality(img_array)
            binarized_versions = self.preprocessor.binarize_images(enhanced_versions)
            
            # Select optimal configurations
            configs = self.optimizer.get_optimal_configs(characteristics)
            
            # Limit versions for performance
            selected_versions = binarized_versions[:2] + [('original_resized', img_array)]
            
            # Try OCR with different configurations
            best_result = ""
            best_confidence = 0
            
            for version_name, processed_img in selected_versions:
                for config_name, lang_combo, description in configs[:4]:  # Limit to 4 configs
                    try:
                        result, confidence = await self._process_single_attempt(
                            processed_img, config_name, lang_combo
                        )
                        
                        if confidence > best_confidence and len(result.strip()) > 10:
                            best_result = result
                            best_confidence = confidence
                            
                            # Early exit for excellent results
                            if confidence > 80:
                                break
                                
                    except Exception as e:
                        logger.debug(f"OCR attempt failed: {e}")
                        continue
            
            processing_time = time.time() - start_time
            
            if best_result and best_confidence > 30:
                performance_monitor.record_request(processing_time, "paragraph_ocr")
                logger.info(f"✅ Paragraph OCR completed in {processing_time:.2f}s, confidence: {best_confidence:.1f}%")
                return best_result
            else:
                performance_monitor.record_error("paragraph_ocr")
                return self._get_error_message(best_confidence)
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "⏱️ Processing took too long. Please try a smaller image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again."
    
    async def _process_single_attempt(self, image: np.ndarray, config_name: str, lang_combo: str) -> Tuple[str, float]:
        """Process single OCR attempt with paragraph detection"""
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            self.executor, self._extract_with_paragraphs, image, config_name, lang_combo
        )
        return result
    
    def _extract_with_paragraphs(self, image: np.ndarray, config_name: str, lang_combo: str) -> Tuple[str, float]:
        """Extract text with advanced paragraph detection"""
        try:
            config = self.optimizer.configs[config_name]
            
            # Get detailed OCR data for paragraph analysis
            data = pytesseract.image_to_data(
                image, 
                lang=lang_combo, 
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            if not confidences:
                return "", 0.0
            
            avg_confidence = sum(confidences) / len(confidences)
            
            # Advanced paragraph reconstruction
            paragraph_text = self._reconstruct_advanced_paragraphs(data, image.shape)
            
            return paragraph_text, avg_confidence
            
        except Exception as e:
            logger.debug(f"Paragraph extraction failed: {e}")
            return "", 0.0
    
    def _reconstruct_advanced_paragraphs(self, data: Dict, image_shape: Tuple[int, int]) -> str:
        """Advanced paragraph reconstruction with intelligent spacing"""
        image_height = image_shape[0]
        
        # Group words by their structural properties
        elements = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            
            if text and confidence > 20:
                elements.append({
                    'text': text,
                    'block_num': data['block_num'][i],
                    'par_num': data['par_num'][i],
                    'line_num': data['line_num'][i],
                    'top': data['top'][i],
                    'left': data['left'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'confidence': confidence
                })
        
        if not elements:
            return ""
        
        # Group elements into lines
        lines = {}
        for element in elements:
            line_key = (element['block_num'], element['par_num'], element['line_num'])
            if line_key not in lines:
                lines[line_key] = []
            lines[line_key].append(element)
        
        # Sort lines by vertical position
        sorted_line_keys = sorted(lines.keys(), key=lambda x: (
            lines[x][0]['top'],  # Sort by top position
            lines[x][0]['left']  # Then by left position
        ))
        
        # Reconstruct paragraphs with intelligent spacing
        paragraphs = []
        current_paragraph = []
        previous_bottom = 0
        previous_right = 0
        
        for line_key in sorted_line_keys:
            line_elements = lines[line_key]
            
            # Sort elements in line by horizontal position
            sorted_elements = sorted(line_elements, key=lambda x: x['left'])
            
            # Reconstruct the line
            line_text = ""
            for i, element in enumerate(sorted_elements):
                # Add spacing based on horizontal gap
                if i > 0:
                    gap = element['left'] - previous_right
                    if gap > element['width'] * 0.8:  # Large gap
                        line_text += '  '
                    else:
                        line_text += ' '
                
                line_text += element['text']
                previous_right = element['left'] + element['width']
            
            current_top = sorted_elements[0]['top']
            current_height = max(el['height'] for el in sorted_elements)
            current_bottom = current_top + current_height
            
            # Paragraph detection logic
            if previous_bottom > 0:
                vertical_gap = current_top - previous_bottom
                
                # Detect paragraph breaks based on:
                # 1. Large vertical gaps (more than 1.5x line height)
                # 2. New block or paragraph numbers
                # 3. Significant horizontal position changes
                is_new_paragraph = (
                    vertical_gap > current_height * 1.5 or
                    line_key[0] != (current_paragraph[-1]['block_num'] if current_paragraph else line_key[0]) or
                    line_key[1] != (current_paragraph[-1]['par_num'] if current_paragraph else line_key[1])
                )
                
                if is_new_paragraph and current_paragraph:
                    # Finalize current paragraph
                    paragraph_text = ' '.join(current_paragraph)
                    if paragraph_text.strip():
                        paragraphs.append(paragraph_text)
                    current_paragraph = []
            
            current_paragraph.append(line_text)
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
            # Fallback to simple extraction
            return self._fallback_simple_extraction(data)
    
    def _fallback_simple_extraction(self, data: Dict) -> str:
        """Fallback method for simple text extraction"""
        text_lines = []
        current_line = []
        last_top = None
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            top = data['top'][i]
            
            if text and conf > 20:
                # Detect line breaks
                if last_top is not None and abs(top - last_top) > 10:
                    if current_line:
                        text_lines.append(' '.join(current_line))
                        current_line = []
                
                current_line.append(text)
                last_top = top
        
        if current_line:
            text_lines.append(' '.join(current_line))
        
        return '\n'.join(text_lines)
    
    def _get_error_message(self, confidence: float) -> str:
        """Get appropriate error message"""
        if confidence > 20:
            return (
                "🔍 Text detected but confidence is low.\n\n"
                "💡 *For better results:*\n"
                "• Use higher contrast images\n"
                "• Ensure text is horizontal\n"
                "• Better lighting conditions\n"
                "• Clear, focused photography"
            )
        else:
            return (
                "❌ No readable text found.\n\n"
                "🎯 *Production Tips:*\n"
                "• Clear, high-contrast images\n"
                "• Sharp, non-blurry text\n"
                "• Good lighting\n"
                "• Horizontal text alignment\n"
                "• Text should be clearly readable"
            )

# Global instances
ocr_processor = AdvancedParagraphOCR()
performance_monitor = PerformanceMonitor()