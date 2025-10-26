# utils/enhanced_ocr.py
import cv2
import numpy as np
import pytesseract
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List
import io
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

class EnhancedOCRProcessor:
    """Enhanced OCR processor with superpower for blurry images"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.setup_enhanced_configs()
        logger.info("✅ Enhanced OCR Processor initialized with blurry image superpower")
    
    def setup_enhanced_configs(self):
        """Enhanced configurations optimized for blurry/low-quality images"""
        self.configs = {
            'blurry_optimized': '--oem 3 --psm 6 -c textord_min_linesize=0.3 -c textord_old_baselines=0 -c textord_noise_rej=0 -c textord_heavy_nr=0',
            'low_quality': '--oem 3 --psm 6 -c textord_min_linesize=0.2 -c textord_old_baselines=1 -c edges_use_new_stored_functions=0',
            'super_blurry': '--oem 3 --psm 8 -c textord_min_linesize=0.1',  # Single word mode for very blurry
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
        }
    
    async def extract_text_enhanced(self, image_bytes: bytes) -> str:
        """Enhanced extraction with superpower for blurry images"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Enhanced preprocessing specifically for blurry images
            processed_imgs = await self._enhanced_preprocessing(image_bytes)
            
            # Try multiple strategies for blurry images
            extracted_text = await self._multi_strategy_extraction(processed_imgs)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            if extracted_text and self._validate_enhanced_text(extracted_text):
                logger.info(f"✅ Enhanced OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                return await self._get_enhanced_fallback(image_bytes)
                
        except Exception as e:
            logger.error(f"Enhanced OCR error: {e}")
            return "Error processing image. Please try again with a clearer image."
    
    async def _enhanced_preprocessing(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Multiple preprocessing strategies for blurry images"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self._apply_enhanced_preprocessing, image_bytes
        )
    
    def _apply_enhanced_preprocessing(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Apply multiple enhancement techniques for blurry images"""
        processed = {}
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                # Fallback to PIL
                image = Image.open(io.BytesIO(image_bytes))
                img = np.array(image.convert('RGB'))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Strategy 1: Basic enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            processed['basic'] = enhanced
            
            # Strategy 2: Sharpening for blurry text
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            processed['sharpened'] = sharpened
            
            # Strategy 3: Bilateral filter (preserves edges)
            bilateral = cv2.bilateralFilter(enhanced, 9, 75, 75)
            processed['bilateral'] = bilateral
            
            # Strategy 4: Morphological operations for very blurry text
            kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
            morph = cv2.morphologyEx(enhanced, cv2.MORPH_CLOSE, kernel_morph)
            processed['morphological'] = morph
            
            # Strategy 5: High contrast for low-quality images
            high_contrast = cv2.convertScaleAbs(enhanced, alpha=1.5, beta=0)
            processed['high_contrast'] = high_contrast
            
            # Strategy 6: Gaussian blur + threshold for noisy images
            gaussian = cv2.GaussianBlur(enhanced, (3,3), 0)
            _, thresh = cv2.threshold(gaussian, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed['threshold'] = thresh
            
        except Exception as e:
            logger.error(f"Enhanced preprocessing error: {e}")
            # Fallback to basic processing
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            processed['fallback'] = np.array(image)
        
        return processed
    
    async def _multi_strategy_extraction(self, processed_imgs: Dict[str, np.ndarray]) -> str:
        """Try multiple extraction strategies for blurry images"""
        loop = asyncio.get_event_loop()
        strategies = []
        
        # Define strategy combinations
        strategy_combinations = [
            # For moderately blurry images
            {'image': 'sharpened', 'config': 'blurry_optimized', 'lang': 'eng+amh'},
            {'image': 'bilateral', 'config': 'blurry_optimized', 'lang': 'eng+amh'},
            {'image': 'basic', 'config': 'low_quality', 'lang': 'eng+amh'},
            
            # For very blurry images
            {'image': 'morphological', 'config': 'super_blurry', 'lang': 'eng'},
            {'image': 'high_contrast', 'config': 'super_blurry', 'lang': 'eng'},
            {'image': 'threshold', 'config': 'super_blurry', 'lang': 'eng'},
            
            # Fallback strategies
            {'image': 'basic', 'config': 'standard', 'lang': 'eng+amh'},
            {'image': 'sharpened', 'config': 'standard', 'lang': 'eng'},
        ]
        
        for strategy in strategy_combinations:
            img_key = strategy['image']
            if img_key in processed_imgs:
                strategies.append(
                    self._extract_with_strategy(
                        processed_imgs[img_key], 
                        strategy['lang'], 
                        strategy['config']
                    )
                )
        
        # Execute all strategies concurrently
        if strategies:
            results = await asyncio.gather(*strategies, return_exceptions=True)
            
            # Find the best result
            best_text = ""
            best_score = 0
            
            for result in results:
                if isinstance(result, str) and result:
                    score = self._calculate_text_quality(result)
                    if score > best_score:
                        best_score = score
                        best_text = result
            
            if best_score > 0.3:  # Reasonable quality threshold
                return best_text
        
        return ""
    
    async def _extract_with_strategy(self, image: np.ndarray, lang: str, config: str) -> str:
        """Extract text with specific strategy"""
        try:
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image, lang, self.configs[config]
            )
            return text.strip() if text else ""
        except Exception as e:
            logger.debug(f"Strategy {lang}-{config} failed: {e}")
            return ""
    
    def _calculate_text_quality(self, text: str) -> float:
        """Calculate quality score for extracted text"""
        if not text or len(text.strip()) < 5:
            return 0.0
        
        clean_text = text.strip()
        score = 0.0
        
        # Length factor (longer is generally better)
        length_factor = min(len(clean_text) / 50.0, 1.0)
        score += length_factor * 0.3
        
        # Character diversity
        unique_chars = len(set(clean_text.replace(' ', '').replace('\n', '')))
        diversity_factor = min(unique_chars / 10.0, 1.0)
        score += diversity_factor * 0.3
        
        # Word count (if applicable)
        words = clean_text.split()
        if len(words) > 1:
            word_factor = min(len(words) / 5.0, 1.0)
            score += word_factor * 0.2
        
        # Line count factor
        lines = [line for line in clean_text.split('\n') if line.strip()]
        line_factor = min(len(lines) / 3.0, 1.0)
        score += line_factor * 0.2
        
        return min(score, 1.0)
    
    def _validate_enhanced_text(self, text: str) -> bool:
        """Enhanced validation for blurry image text"""
        if not text:
            return False
        
        clean_text = text.strip()
        
        # More lenient validation for blurry images
        if len(clean_text) < 3:  # Reduced from 10 to 3
            return False
        
        # Check for basic character diversity
        text_chars = clean_text.replace(' ', '').replace('\n', '')
        if len(text_chars) == 0:
            return False
        
        unique_chars = len(set(text_chars))
        if unique_chars < 2:  # Reduced threshold
            return False
        
        return True
    
    async def _get_enhanced_fallback(self, image_bytes: bytes) -> str:
        """Final fallback attempt with different approach"""
        try:
            # Try with simple PIL preprocessing
            image = Image.open(io.BytesIO(image_bytes))
            
            # Multiple enhancement attempts
            enhancements = [
                lambda img: img,
                lambda img: ImageEnhance.Contrast(img).enhance(2.0),
                lambda img: ImageEnhance.Sharpness(img).enhance(2.0),
                lambda img: ImageEnhance.Brightness(img).enhance(1.2),
            ]
            
            for enhance_func in enhancements:
                try:
                    enhanced_img = enhance_func(image.convert('L'))
                    text = pytesseract.image_to_string(
                        enhanced_img, 
                        lang='eng',
                        config='--oem 3 --psm 8'  # Single word mode
                    )
                    if text and len(text.strip()) >= 3:
                        return text.strip()
                except:
                    continue
            
            return "No readable text could be extracted. Please try with a clearer image."
            
        except Exception as e:
            logger.error(f"Enhanced fallback failed: {e}")
            return "Unable to process this image. Please try with a clearer, well-lit image."

# Global instance
enhanced_ocr_processor = EnhancedOCRProcessor()