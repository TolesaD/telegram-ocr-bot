# utils/smart_ocr.py (UPDATED VERSION)
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
    """ENHANCED OCR processor - Better accuracy and quality"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.available_languages = self._get_available_languages()
        self.setup_enhanced_configs()
        logger.info(f"✅ ENHANCED OCR Processor ready with {len(self.available_languages)} languages")
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng', 'amh']
    
    def setup_enhanced_configs(self):
        """Enhanced configurations for better accuracy"""
        self.configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c tessedit_pageseg_mode=6',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_block': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7 -c preserve_interword_spaces=1',
            'single_word': '--oem 3 --psm 8 -c preserve_interword_spaces=1',
            'high_accuracy': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c textord_min_linesize=1.5',
        }
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """ENHANCED OCR extraction - Better accuracy and quality"""
        start_time = time.time()
        
        try:
            # Enhanced preprocessing
            processed_imgs = await self._enhanced_preprocessing(image_bytes)
            
            # Multi-strategy extraction for better accuracy
            extracted_text = await self._accuracy_optimized_extraction(processed_imgs)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_quality_text(extracted_text):
                logger.info(f"✅ ENHANCED OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return self._post_process_text(extracted_text)
            else:
                # Try fallback strategies
                fallback_text = await self._fallback_extraction(image_bytes)
                return fallback_text if fallback_text else "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _enhanced_preprocessing(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Multiple preprocessing strategies for better accuracy"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._apply_enhanced_preprocessing, image_bytes
        )
    
    def _apply_enhanced_preprocessing(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Apply multiple preprocessing techniques"""
        processed = {}
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                image = Image.open(io.BytesIO(image_bytes))
                img = np.array(image.convert('RGB'))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Strategy 1: Basic enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            processed['basic'] = enhanced
            
            # Strategy 2: Noise reduction + sharpening
            denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            processed['sharpened'] = sharpened
            
            # Strategy 3: High contrast for better character recognition
            high_contrast = cv2.convertScaleAbs(enhanced, alpha=1.3, beta=10)
            processed['high_contrast'] = high_contrast
            
            # Strategy 4: Morphological operations for clean text
            kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
            morph = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel_morph)
            processed['morphological'] = morph
            
            # Strategy 5: Adaptive threshold for varying lighting
            adaptive_thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            processed['adaptive_thresh'] = adaptive_thresh
            
        except Exception as e:
            logger.error(f"Enhanced preprocessing error: {e}")
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            processed['fallback'] = np.array(image)
        
        return processed
    
    async def _accuracy_optimized_extraction(self, processed_imgs: Dict[str, np.ndarray]) -> str:
        """Accuracy-optimized extraction with multiple strategies"""
        loop = asyncio.get_event_loop()
        
        # Priority language combinations for accuracy
        language_combinations = [
            'eng+amh',  # Primary combination
            'amh+eng',  # Alternative order
            'eng',      # English only
            'amh',      # Amharic only
            self._get_optimized_language_group(),  # Optimized group
        ]
        
        # Try different preprocessing + language combinations
        best_result = {"text": "", "confidence": 0}
        
        for img_key, image in processed_imgs.items():
            for lang_combo in language_combinations:
                for config_name in ['high_accuracy', 'standard', 'document']:
                    try:
                        text = await loop.run_in_executor(
                            self.executor,
                            pytesseract.image_to_string,
                            image, lang_combo, self.configs[config_name]
                        )
                        
                        if text and self._is_quality_text(text):
                            confidence = self._calculate_confidence(text, lang_combo)
                            
                            if confidence > best_result["confidence"]:
                                best_result = {
                                    "text": text.strip(),
                                    "confidence": confidence
                                }
                                
                            # Early exit for high confidence
                            if confidence > 0.8:
                                return best_result["text"]
                                
                    except Exception as e:
                        continue
        
        return best_result["text"]
    
    def _get_optimized_language_group(self) -> str:
        """Create optimized language group for accuracy"""
        priority_languages = [
            'eng', 'amh', 'ara', 'spa', 'fra', 'deu', 'ita', 'por',
            'rus', 'jpn', 'kor', 'chi_sim', 'hin'
        ]
        
        available = [lang for lang in priority_languages if lang in self.available_languages]
        return '+'.join(available[:5]) if available else 'eng'
    
    def _calculate_confidence(self, text: str, lang_used: str) -> float:
        """Calculate confidence score for extracted text"""
        if not text:
            return 0.0
        
        clean_text = text.strip()
        score = 0.0
        
        # Basic length factor
        length_score = min(len(clean_text) / 100.0, 1.0)
        score += length_score * 0.3
        
        # Character diversity
        unique_chars = len(set(clean_text.replace(' ', '').replace('\n', '')))
        diversity_score = min(unique_chars / 15.0, 1.0)
        score += diversity_score * 0.3
        
        # Word and line structure
        words = clean_text.split()
        lines = [line for line in clean_text.split('\n') if line.strip()]
        
        if len(words) > 2:
            score += 0.2
        if len(lines) > 1:
            score += 0.2
        
        return min(score, 1.0)
    
    def _is_quality_text(self, text: str) -> bool:
        """Enhanced quality validation"""
        if not text:
            return False
        
        clean_text = text.strip()
        
        # Basic checks
        if len(clean_text) < 8:
            return False
        
        # Character diversity check
        text_chars = clean_text.replace(' ', '').replace('\n', '')
        if len(text_chars) < 5:
            return False
        
        unique_chars = len(set(text_chars))
        if unique_chars < 3:
            return False
        
        # Check for reasonable word/line structure
        words = clean_text.split()
        if len(words) == 1 and len(words[0]) < 4:
            return False
        
        # Check for excessive repetition
        if len(clean_text) > 20:
            char_counts = {}
            for char in clean_text:
                if char.isalnum():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                max_count = max(char_counts.values())
                if max_count / len(clean_text) > 0.4:
                    return False
        
        return True
    
    def _post_process_text(self, text: str) -> str:
        """Post-process extracted text for better quality"""
        if not text:
            return text
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Clean up common OCR artifacts
                line = re.sub(r'\s+', ' ', line)  # Normalize spaces
                line = re.sub(r'[ \t]{2,}', ' ', line)  # Remove multiple spaces/tabs
                processed_lines.append(line)
        
        # Reconstruct text with proper paragraph separation
        result = '\n'.join(processed_lines)
        
        # Final cleanup
        result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 consecutive newlines
        
        return result
    
    async def _fallback_extraction(self, image_bytes: bytes) -> str:
        """Comprehensive fallback extraction"""
        try:
            # Try simple PIL-based approach
            image = Image.open(io.BytesIO(image_bytes))
            
            # Multiple enhancement attempts
            for contrast in [1.5, 2.0, 1.0]:
                for sharpness in [1.5, 2.0, 1.0]:
                    try:
                        enhanced = ImageEnhance.Contrast(image).enhance(contrast)
                        enhanced = ImageEnhance.Sharpness(enhanced).enhance(sharpness)
                        
                        text = pytesseract.image_to_string(
                            enhanced.convert('L'),
                            lang='eng',
                            config=self.configs['single_block']
                        )
                        
                        if text and self._is_quality_text(text):
                            return self._post_process_text(text)
                    except:
                        continue
            
            return ""
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return ""

# Global instance
smart_ocr_processor = SmartOCRProcessor()