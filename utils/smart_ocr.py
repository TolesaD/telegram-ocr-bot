# utils/smart_ocr.py - SUPER POWER VERSION
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
    """SUPER POWER OCR processor - Enhanced for blurry images and global languages"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.available_languages = self._get_available_languages()
        self.setup_enhanced_configs()
        logger.info(f"🚀 SUPER POWER OCR Processor ready with {len(self.available_languages)} languages")
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)}")
            if langs:
                logger.info(f"📋 Languages: {', '.join(langs[:10])}{'...' if len(langs) > 10 else ''}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor', 'rus', 'hin', 'spa', 'fra', 'deu']
    
    def setup_enhanced_configs(self):
        """Enhanced OCR configurations for blurry images and better accuracy"""
        self.configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'blurry': '--oem 3 --psm 6 -c textord_min_linesize=0.5 -c textord_old_xheight=1',
            'single_line': '--oem 3 --psm 7',
            'single_word': '--oem 3 --psm 8',
            'amharic_optimized': '--oem 3 --psm 6 -c textord_min_linesize=1.8 -c preserve_interword_spaces=1',
        }
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """SUPER POWER OCR extraction - Enhanced for blurry images"""
        start_time = time.time()
        
        try:
            # Step 1: Generate multiple preprocessing variations for blurry images
            processed_variations = await self._advanced_preprocess(image_bytes)
            
            # Step 2: Multi-strategy extraction with voting system
            extracted_text = await self._super_extraction_strategy(processed_variations)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_high_quality_text(extracted_text):
                logger.info(f"✅ SUPER POWER OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                # Analyze why extraction failed
                quality_info = await self._analyze_image_quality(image_bytes)
                return self._get_intelligent_error_message(quality_info)
                
        except asyncio.TimeoutError:
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _advanced_preprocess(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Advanced preprocessing with multiple strategies for blurry images"""
        variations = {}
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Original grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            variations['original'] = gray
            
            # === BLURRY IMAGE ENHANCEMENT STRATEGIES ===
            
            # Strategy 1: CLAHE for contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            variations['clahe'] = clahe.apply(gray)
            
            # Strategy 2: Unsharp masking for blurry images (SUPER POWER)
            gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
            variations['unsharp'] = cv2.addWeighted(gray, 2.5, gaussian, -1.5, 0)
            
            # Strategy 3: Bilateral filter for noise reduction while preserving edges
            variations['bilateral'] = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Strategy 4: Morphological operations for text enhancement
            kernel = np.ones((2, 2), np.uint8)
            variations['morph'] = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Strategy 5: Adaptive threshold for varying lighting
            variations['adaptive'] = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Strategy 6: Denoising
            variations['denoised'] = cv2.fastNlMeansDenoising(gray, h=10)
            
            # Strategy 7: Resize for small/blurry text
            height, width = gray.shape
            if height < 600 or width < 600:
                variations['resized_2x'] = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            if height > 2000 or width > 2000:
                variations['resized_half'] = cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            
            logger.info(f"✅ Generated {len(variations)} preprocessing variations for blurry images")
            
        except Exception as e:
            logger.error(f"Advanced preprocessing failed: {e}")
            # Fallback to basic processing
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            variations['fallback'] = np.array(image)
        
        return variations
    
    async def _super_extraction_strategy(self, variations: Dict[str, np.ndarray]) -> str:
        """Multi-strategy extraction with intelligent voting for blurry images"""
        loop = asyncio.get_event_loop()
        all_results = []
        
        # Define comprehensive language strategies
        language_strategies = [
            ('eng+amh', 'standard'),      # English + Amharic
            ('eng', 'standard'),          # English only
            ('amh', 'amharic_optimized'), # Amharic optimized
            ('eng+amh+ara', 'standard'),  # Multiple languages
            ('', 'standard'),             # Auto-detect
        ]
        
        # Enhanced blurry image strategies
        blurry_strategies = [
            ('eng+amh', 'blurry'),
            ('eng', 'blurry'),
            ('amh', 'blurry'),
        ]
        
        # Try each preprocessing variation with each language strategy
        for img_name, image in variations.items():
            # Use blurry strategies for blurry-enhancement preprocessing
            strategies_to_try = blurry_strategies if any(x in img_name for x in ['unsharp', 'bilateral', 'resized']) else language_strategies
            
            for lang_group, config_name in strategies_to_try:
                try:
                    config = self.configs.get(config_name, self.configs['standard'])
                    
                    text = await loop.run_in_executor(
                        self.executor,
                        pytesseract.image_to_string,
                        image, lang_group, config
                    )
                    
                    if text and self._is_quality_text(text):
                        confidence = self._calculate_enhanced_confidence(text, lang_group, img_name)
                        all_results.append({
                            'text': text.strip(),
                            'confidence': confidence,
                            'strategy': f"{img_name}+{lang_group}",
                            'length': len(text.strip())
                        })
                        
                        logger.debug(f"✅ Strategy: {img_name}+{lang_group} - {len(text.strip())} chars, conf: {confidence:.2f}")
                        
                except Exception as e:
                    logger.debug(f"Strategy {img_name}+{lang_group} failed: {e}")
                    continue
        
        # Select best result using advanced scoring
        if all_results:
            return self._select_best_result_enhanced(all_results)
        
        return ""
    
    def _calculate_enhanced_confidence(self, text: str, lang_group: str, strategy: str) -> float:
        """Enhanced confidence calculation with blurry image bonuses"""
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
        
        # Blurry strategy bonus (SUPER POWER)
        if any(x in strategy for x in ['unsharp', 'bilateral', 'resized']):
            base_score += 0.15  # Bonus for blurry image techniques
        
        # Language-specific validation
        if 'amh' in lang_group:
            # Amharic character detection
            amharic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137f')
            if amharic_chars >= 3:
                base_score += 0.2
        
        # Word count and structure
        words = clean_text.split()
        if len(words) >= 3:
            base_score += 0.1
        
        # Line structure bonus
        lines = [line for line in clean_text.split('\n') if line.strip()]
        if len(lines) >= 2:
            base_score += 0.05
        
        return min(base_score, 1.0)
    
    def _select_best_result_enhanced(self, results: List[Dict]) -> str:
        """Enhanced result selection with blurry image preference"""
        if not results:
            return ""
        
        # Remove exact duplicates
        unique_results = {}
        for result in results:
            text = result['text']
            if text not in unique_results or result['confidence'] > unique_results[text]['confidence']:
                unique_results[text] = result
        
        unique_list = list(unique_results.values())
        
        # Score each result with enhanced criteria
        scored_results = []
        for result in unique_list:
            score = result['confidence']
            
            # Length bonus (optimal range)
            length = result['length']
            if 20 <= length <= 2000:
                score += 0.2
            elif length > 2000:
                score += 0.1
            
            # Blurry strategy super bonus
            if any(x in result['strategy'] for x in ['unsharp', 'bilateral', 'resized']):
                score += 0.2  # Higher bonus for successful blurry extraction
            
            # Language combination bonus
            if '+' in result['strategy'] and 'eng' in result['strategy']:
                score += 0.1
            
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return the highest scored result
        best_score, best_result = scored_results[0]
        
        logger.info(f"🏆 SUPER POWER Selected: {best_result['strategy']} - score: {best_score:.2f}, length: {best_result['length']}")
        return best_result['text']
    
    async def _analyze_image_quality(self, image_bytes: bytes) -> Dict[str, any]:
        """Analyze image quality to provide intelligent error messages"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "Failed to decode image"}
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Blur detection
            blur_value = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Contrast and brightness
            contrast = gray.std()
            brightness = gray.mean()
            
            # Edge detection for text presence
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            return {
                "blur": blur_value,
                "contrast": contrast,
                "brightness": brightness,
                "edge_density": edge_density,
                "is_blurry": blur_value < 30,
                "is_dark": brightness < 60,
                "is_low_contrast": contrast < 25,
                "has_edges": edge_density > 0.01
            }
            
        except Exception as e:
            logger.error(f"Image quality analysis failed: {e}")
            return {"error": "Analysis failed"}
    
    def _get_intelligent_error_message(self, quality_info: Dict[str, any]) -> str:
        """Provide intelligent error messages based on image analysis"""
        if "error" in quality_info:
            return "❌ No readable text found. Please ensure the image contains clear, focused text."
        
        if quality_info.get('is_blurry', False):
            return "❌ Image is too blurry. 📸 **Try this:**\n• Hold camera steady\n• Ensure good lighting\n• Focus on the text\n• Avoid camera shake"
        
        elif quality_info.get('is_dark', False):
            return "❌ Image is too dark. 💡 **Try this:**\n• Use better lighting\n• Avoid shadows\n• Natural light works best\n• No flash glare"
        
        elif quality_info.get('is_low_contrast', False):
            return "❌ Low contrast between text and background. 🎨 **Try this:**\n• Ensure text stands out\n• Use plain backgrounds\n• Avoid similar colors\n• Increase contrast"
        
        elif not quality_info.get('has_edges', False):
            return "❌ No text detected in image. 🔍 **Try this:**\n• Ensure image contains text\n• Text should be clear and readable\n• Avoid handwritten text\n• Use printed documents"
        
        else:
            return "❌ No readable text found. Please ensure the image contains clear, focused text."
    
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
        
        # Check for excessive repetition (garbage detection)
        if len(clean_text) > 10:
            char_counts = {}
            for char in clean_text:
                if char.isalnum():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                max_count = max(char_counts.values())
                if max_count / len(clean_text) > 0.7:
                    return False
        
        # Check for meaningful content (reduced threshold for global languages)
        alpha_chars = sum(1 for c in clean_text if c.isalpha())
        total_chars = len(clean_text)
        
        if total_chars > 0 and alpha_chars / total_chars < 0.15:
            return False
        
        return True

# Global instance
smart_ocr_processor = SmartOCRProcessor()