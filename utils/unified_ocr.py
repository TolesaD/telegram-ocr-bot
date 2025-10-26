# utils/unified_ocr.py - CREATE THIS NEW FILE
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
import time
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Any
import io
from PIL import Image, ImageEnhance, ImageFilter
import re

logger = logging.getLogger(__name__)

# Configure Tesseract path
TESSERACT_CMD = '/usr/bin/tesseract'
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    logger.info(f"✅ Tesseract configured at: {TESSERACT_CMD}")

class UltimateOCRProcessor:
    """ULTIMATE OCR Processor - Combines best of both worlds for global language support"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.available_languages = self._get_available_languages()
        self.setup_ultimate_configs()
        logger.info(f"🚀 ULTIMATE OCR Processor ready with {len(self.available_languages)} languages")
        
    def _get_available_languages(self) -> List[str]:
        """Get all available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            # Return comprehensive language list
            return ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor', 'rus', 'hin', 'spa', 'fra', 'deu', 'ita', 'por', 'tur', 'vie', 'tha']
    
    def setup_ultimate_configs(self):
        """Ultimate OCR configurations optimized for all languages"""
        self.configs = {
            # Universal configurations
            'universal': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c tessedit_do_invert=0',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7',
            'single_word': '--oem 3 --psm 8',
            
            # Language-specific optimizations
            'amharic_optimized': '--oem 3 --psm 6 -c textord_min_linesize=1.8 -c preserve_interword_spaces=1',
            'arabic_optimized': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c textord_arabic_normstr=1',
            'chinese_optimized': '--oem 3 --psm 6 -c preserve_interword_spaces=0 -c textord_really_old_xheight=1',
            
            # Blurry image optimizations
            'blurry_enhanced': '--oem 3 --psm 6 -c textord_min_linesize=0.5 -c textord_old_xheight=1',
        }
    
    async def extract_text_ultimate(self, image_bytes: bytes) -> str:
        """ULTIMATE OCR extraction with multi-strategy approach"""
        start_time = time.time()
        
        try:
            # Step 1: Generate multiple preprocessing variations
            processed_variations = await self._generate_preprocessing_variations(image_bytes)
            
            # Step 2: Multi-strategy extraction with voting
            extracted_text = await self._ultimate_extraction_strategy(processed_variations)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_high_quality_text(extracted_text):
                logger.info(f"✅ ULTIMATE OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"ULTIMATE OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _generate_preprocessing_variations(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Generate multiple preprocessing variations for different scenarios"""
        variations = {}
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Original grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            variations['original'] = gray
            
            # Enhanced preprocessing strategies
            preprocessing_strategies = [
                ('clahe', self._apply_clahe_enhancement),
                ('unsharp', self._apply_unsharp_masking),
                ('bilateral', self._apply_bilateral_filter),
                ('morphological', self._apply_morphological_ops),
                ('adaptive_thresh', self._apply_adaptive_threshold),
                ('denoised', self._apply_advanced_denoising),
                ('contrast_boost', self._apply_contrast_boost),
            ]
            
            for name, processor in preprocessing_strategies:
                try:
                    variations[name] = processor(gray)
                except Exception as e:
                    logger.debug(f"Preprocessing {name} failed: {e}")
                    continue
            
            # Resize strategies for small/blurry text
            height, width = gray.shape
            if height < 600 or width < 600:
                variations['resized_2x'] = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            if height > 2000 or width > 2000:
                variations['resized_half'] = cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            
            logger.info(f"✅ Generated {len(variations)} preprocessing variations")
            
        except Exception as e:
            logger.error(f"Preprocessing variations failed: {e}")
            # Fallback to basic processing
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            variations['fallback'] = np.array(image)
        
        return variations
    
    # Enhanced preprocessing methods
    def _apply_clahe_enhancement(self, image: np.ndarray) -> np.ndarray:
        """Apply CLAHE for contrast enhancement"""
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    
    def _apply_unsharp_masking(self, image: np.ndarray) -> np.ndarray:
        """Apply unsharp masking for blurry images"""
        gaussian = cv2.GaussianBlur(image, (0, 0), 2.0)
        return cv2.addWeighted(image, 2.5, gaussian, -1.5, 0)
    
    def _apply_bilateral_filter(self, image: np.ndarray) -> np.ndarray:
        """Apply bilateral filter for noise reduction"""
        return cv2.bilateralFilter(image, 9, 75, 75)
    
    def _apply_morphological_ops(self, image: np.ndarray) -> np.ndarray:
        """Apply morphological operations for text enhancement"""
        kernel = np.ones((2, 2), np.uint8)
        return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    
    def _apply_adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Apply adaptive threshold for varying lighting"""
        return cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
    
    def _apply_advanced_denoising(self, image: np.ndarray) -> np.ndarray:
        """Apply advanced denoising"""
        return cv2.fastNlMeansDenoising(image, h=10)
    
    def _apply_contrast_boost(self, image: np.ndarray) -> np.ndarray:
        """Apply contrast boost"""
        return cv2.convertScaleAbs(image, alpha=1.5, beta=0)
    
    async def _ultimate_extraction_strategy(self, variations: Dict[str, np.ndarray]) -> str:
        """Ultimate extraction strategy with intelligent voting"""
        loop = asyncio.get_event_loop()
        all_results = []
        
        # Define comprehensive language strategies
        language_strategies = self._get_comprehensive_language_strategies()
        
        # Try each preprocessing variation with each language strategy
        for img_name, image in variations.items():
            for lang_group, config_name in language_strategies:
                try:
                    config = self.configs.get(config_name, self.configs['universal'])
                    
                    text = await loop.run_in_executor(
                        self.executor,
                        pytesseract.image_to_string,
                        image, lang_group, config
                    )
                    
                    if text and self._is_quality_text(text):
                        confidence = self._calculate_text_confidence(text, lang_group)
                        all_results.append({
                            'text': text.strip(),
                            'confidence': confidence,
                            'strategy': f"{img_name}+{lang_group}",
                            'length': len(text.strip())
                        })
                        
                        logger.debug(f"✅ Strategy success: {img_name} + {lang_group} - {len(text.strip())} chars, conf: {confidence:.2f}")
                        
                except Exception as e:
                    logger.debug(f"Strategy {img_name}+{lang_group} failed: {e}")
                    continue
        
        # Select best result using advanced scoring
        if all_results:
            return self._select_best_result_advanced(all_results)
        
        return ""
    
    def _get_comprehensive_language_strategies(self) -> List[Tuple[str, str]]:
        """Get comprehensive language strategies for global support"""
        strategies = []
        
        # Universal language groups
        universal_groups = [
            ('eng+amh+ara+chi_sim+jpn+kor+rus+hin+spa+fra', 'universal'),
            ('eng+amh+ara', 'universal'),
            ('amh+eng', 'amharic_optimized'),
            ('ara+eng', 'arabic_optimized'),
            ('chi_sim+eng', 'chinese_optimized'),
        ]
        
        # Individual major languages
        major_languages = ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor', 'rus', 'hin', 'spa', 'fra', 'deu', 'ita', 'por', 'tur', 'vie', 'tha']
        
        for lang in major_languages:
            if lang in self.available_languages:
                config = 'universal'
                if lang == 'amh':
                    config = 'amharic_optimized'
                elif lang == 'ara':
                    config = 'arabic_optimized'
                elif lang == 'chi_sim':
                    config = 'chinese_optimized'
                strategies.append((lang, config))
        
        # Add blurry-optimized strategies
        strategies.extend([
            ('eng+amh', 'blurry_enhanced'),
            ('eng', 'blurry_enhanced'),
            ('amh', 'blurry_enhanced'),
        ])
        
        return strategies
    
    def _select_best_result_advanced(self, results: List[Dict]) -> str:
        """Advanced result selection with multiple quality metrics"""
        if not results:
            return ""
        
        # Remove exact duplicates
        unique_results = {}
        for result in results:
            text = result['text']
            if text not in unique_results or result['confidence'] > unique_results[text]['confidence']:
                unique_results[text] = result
        
        unique_list = list(unique_results.values())
        
        # Score each result
        scored_results = []
        for result in unique_list:
            score = self._calculate_comprehensive_score(result)
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return the highest scored result
        best_score, best_result = scored_results[0]
        
        logger.info(f"🏆 Selected best result: {best_result['strategy']} - score: {best_score:.2f}, length: {best_result['length']}")
        return best_result['text']
    
    def _calculate_comprehensive_score(self, result: Dict) -> float:
        """Calculate comprehensive quality score"""
        text = result['text']
        base_confidence = result['confidence']
        length = result['length']
        
        score = base_confidence * 0.4  # 40% base confidence
        
        # Length factor (optimal range)
        if 20 <= length <= 2000:
            score += 0.3
        elif length > 2000:
            score += 0.2
        else:
            score += 0.1
        
        # Character diversity
        unique_chars = len(set(text))
        diversity_ratio = unique_chars / length if length > 0 else 0
        if diversity_ratio > 0.4:
            score += 0.2
        elif diversity_ratio > 0.2:
            score += 0.15
        else:
            score += 0.05
        
        # Structure quality
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) >= 2:
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            if 10 <= avg_line_length <= 100:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_text_confidence(self, text: str, lang_group: str) -> float:
        """Calculate confidence score for extracted text"""
        if not text:
            return 0.0
        
        clean_text = text.strip()
        length = len(clean_text)
        
        if length < 5:
            return 0.1
        
        base_score = 0.3
        
        # Length factor
        length_factor = min(length / 100, 0.3)
        base_score += length_factor
        
        # Character diversity
        unique_chars = len(set(clean_text))
        diversity_factor = min(unique_chars / 15, 0.2)
        base_score += diversity_factor
        
        # Language-specific validation
        if 'amh' in lang_group:
            # Amharic validation
            amharic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137f')
            if amharic_chars >= 3:
                base_score += 0.2
        
        # Word count factor
        words = re.findall(r'\b\w+\b', clean_text)
        if len(words) >= 3:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _is_high_quality_text(self, text: str) -> bool:
        """Check if text is high quality"""
        return self._is_quality_text(text) and len(text.strip()) >= 10
    
    def _is_quality_text(self, text: str) -> bool:
        """Enhanced text quality validation"""
        if not text:
            return False
        
        clean_text = text.strip()
        
        # Basic length check
        if len(clean_text) < 3:
            return False
        
        # Character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 2:
            return False
        
        # Check for excessive repetition
        if len(clean_text) > 10:
            char_counts = {}
            for char in clean_text:
                if char.isalnum():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                max_count = max(char_counts.values())
                if max_count / len(clean_text) > 0.7:  # 70% same character
                    return False
        
        # Check for meaningful content
        alpha_chars = sum(1 for c in clean_text if c.isalpha())
        total_chars = len(clean_text)
        
        if total_chars > 0 and alpha_chars / total_chars < 0.15:  # Reduced threshold for global languages
            return False
        
        return True

# Global instance
ultimate_ocr_processor = UltimateOCRProcessor()