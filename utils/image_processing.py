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
import os

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
            'paragraph': f"{base_config} --psm 6 -c preserve_interword_spaces=1 -c textord_min_linesize=1.0 -c textord_tabfind_vertical_text=0"
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
        
        # Remove duplicates and limit to 8 configurations for performance
        unique_configs = list(dict.fromkeys(configs_to_try))
        return unique_configs[:8]

class ParagraphOCRProcessor:
    """Advanced OCR processor with paragraph structure detection"""
    
    def __init__(self):
        self.preprocessor = AdvancedImagePreprocessor()
        self.optimizer = TesseractOptimizer()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.cache = {}
        
    async def extract_text_optimized(self, image_bytes: bytes) -> str:
        """Advanced text extraction with paragraph structure preservation"""
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
            
            # Limit versions for performance (take best 3)
            selected_versions = binarized_versions[:3] + [('original_resized', img_array)]
            
            # Create all OCR tasks properly
            tasks = []
            for img_name, processed_img in selected_versions:
                for config_name, lang_combo, description in configs:
                    # Create task for each combination
                    task = asyncio.create_task(
                        self._process_single_attempt(
                            processed_img, config_name, lang_combo, description
                        )
                    )
                    tasks.append(task)
            
            # Wait for all tasks with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=20.0
                )
            except asyncio.TimeoutError:
                # Cancel all pending tasks
                for task in tasks:
                    task.cancel()
                raise
            
            # Process results
            successful_results = []
            for result in results:
                if isinstance(result, tuple) and len(result) == 3:
                    text, confidence, description = result
                    if text and confidence > 40:
                        successful_results.append((text, confidence, description))
                elif isinstance(result, Exception):
                    logger.debug(f"OCR task failed: {result}")
            
            # Select best result
            best_text = self._select_best_result(successful_results, characteristics)
            
            processing_time = time.time() - start_time
            
            if best_text:
                performance_monitor.record_request(processing_time, "paragraph_ocr")
                logger.info(f"✅ Paragraph OCR success in {processing_time:.2f}s. Configs: {len(configs)}, Best confidence: {max([r[1] for r in successful_results]) if successful_results else 0}")
                return best_text
            else:
                performance_monitor.record_error("paragraph_ocr")
                return "No readable text found. Please try a clearer image with better lighting and contrast."
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "Processing timeout. Please try a smaller image or better quality."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again."
    
    async def _process_single_attempt(self, image: np.ndarray, config_name: str, 
                                    lang_combo: str, description: str) -> Tuple[str, float, str]:
        """Process single OCR attempt with paragraph detection"""
        loop = asyncio.get_event_loop()
        try:
            # Run the synchronous Tesseract function in thread pool
            result = await loop.run_in_executor(
                self.executor, 
                self._run_paragraph_ocr, 
                image, config_name, lang_combo, description
            )
            return result
        except Exception as e:
            logger.debug(f"OCR task failed for {description}: {e}")
            return "", 0.0, description
    
    def _run_paragraph_ocr(self, image: np.ndarray, config_name: str, 
                          lang_combo: str, description: str) -> Tuple[str, float, str]:
        """Run Tesseract OCR with paragraph structure detection"""
        try:
            config = self.optimizer.configs[config_name]
            
            # Get detailed data for paragraph reconstruction
            data = pytesseract.image_to_data(
                image, 
                lang=lang_combo, 
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate confidence
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            if not confidences:
                return "", 0.0, description
            
            avg_confidence = sum(confidences) / len(confidences)
            
            # Reconstruct text with proper paragraph structure
            extracted_text = self._reconstruct_paragraph_structure(data)
            
            return extracted_text, avg_confidence, description
            
        except Exception as e:
            logger.debug(f"Tesseract failed for {description}: {e}")
            return "", 0.0, description
    
    def _reconstruct_paragraph_structure(self, data: Dict) -> str:
        """Reconstruct text with proper paragraph structure"""
        paragraphs = []
        current_paragraph = []
        current_block = -1
        previous_bottom = 0
        paragraph_gap_threshold = 25  # pixels between paragraphs
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            confidence = int(data['conf'][i])
            block_num = data['block_num'][i]
            par_num = data['par_num'][i]
            line_num = data['line_num'][i]
            top = data['top'][i]
            height = data['height'][i]
            left = data['left'][i]
            width = data['width'][i]
            
            if text and confidence > 20:  # Lower threshold to capture more text
                current_bottom = top + height
                
                # Check for new paragraph based on:
                # 1. New block number
                # 2. Significant vertical gap
                # 3. New paragraph number
                is_new_paragraph = (
                    block_num != current_block or
                    (previous_bottom > 0 and top - previous_bottom > paragraph_gap_threshold) or
                    par_num != current_block
                )
                
                if is_new_paragraph and current_paragraph:
                    # Finalize current paragraph
                    paragraph_text = ' '.join(current_paragraph)
                    if paragraph_text.strip():
                        paragraphs.append(paragraph_text)
                    current_paragraph = []
                
                # Add text to current paragraph
                current_paragraph.append(text)
                current_block = block_num
                previous_bottom = current_bottom
        
        # Add the final paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            if paragraph_text.strip():
                paragraphs.append(paragraph_text)
        
        # Join paragraphs with double newlines for proper separation
        if paragraphs:
            return '\n\n'.join(paragraphs)
        else:
            # Fallback to simple extraction if paragraph detection fails
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
    
    def _select_best_result(self, results: List[Tuple[str, float, str]], 
                          characteristics: Dict) -> str:
        """Intelligently select the best OCR result"""
        if not results:
            return ""
        
        # Filter valid results
        valid_results = [(text, conf, desc) for text, conf, desc in results 
                        if text and len(text.strip()) > 10 and conf > 40]
        
        if not valid_results:
            return ""
        
        # Sort by confidence and text quality
        valid_results.sort(key=lambda x: (x[1], self._calculate_text_quality(x[0])), reverse=True)
        
        # Take the best result
        best_text, best_conf, best_desc = valid_results[0]
        
        logger.info(f"Selected result: {best_desc} with confidence {best_conf:.1f}")
        
        return best_text
    
    def _calculate_text_quality(self, text: str) -> float:
        """Calculate text quality score based on paragraph structure"""
        if not text:
            return 0.0
        
        # Count paragraphs
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        # Calculate average words per paragraph
        words = text.split()
        word_count = len(words)
        
        if paragraph_count == 0 or word_count == 0:
            return 0.0
        
        avg_words_per_paragraph = word_count / paragraph_count
        
        # Quality score favors well-structured text with reasonable paragraph length
        if avg_words_per_paragraph > 5 and avg_words_per_paragraph < 100:
            structure_score = 0.7
        else:
            structure_score = 0.3
        
        # Combine with basic text quality
        unique_chars = len(set(text.replace(' ', '').replace('\n', '')))
        diversity_score = unique_chars / len(text) if text else 0
        
        return (structure_score * 0.6) + (diversity_score * 0.4)

# Global instances
ocr_processor = ParagraphOCRProcessor()
performance_monitor = PerformanceMonitor()