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
    """Universal OCR processor with robust language detection"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.available_languages = self._get_available_languages()
        self.setup_ocr_configs()
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)} languages")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng', 'amh']  # Fallback to basic languages
    
    def setup_ocr_configs(self):
        """Optimized OCR configurations for universal language support"""
        self.configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7 -c preserve_interword_spaces=1',
            'sparse_text': '--oem 3 --psm 6 -c textord_min_linesize=0.5',
            'blurry': '--oem 3 --psm 6 -c textord_old_baselines=1',
            'quick_detect': '--oem 3 --psm 6'  # For language detection
        }
        
        # Language scripts grouped by writing system
        self.language_scripts = {
            'latin': ['eng', 'fra', 'spa', 'deu', 'ita', 'por', 'nld', 'swe', 'dan', 'nor', 'fin', 'pol', 'ces', 'hun', 'ron', 'hrv', 'srp', 'slk', 'slv', 'lav', 'lit', 'est', 'lav', 'glg', 'cat', 'eus'],
            'ethiopic': ['amh', 'tir', 'orm'],
            'arabic': ['ara', 'fas', 'urd', 'uig'],
            'chinese': ['chi_sim', 'chi_tra'],
            'japanese': ['jpn'],
            'korean': ['kor'],
            'devanagari': ['hin', 'nep', 'mar', 'san'],
            'bengali': ['ben'],
            'hebrew': ['heb'],
            'thai': ['tha'],
            'vietnamese': ['vie'],
            'cyrillic': ['rus', 'ukr', 'bul', 'bel', 'srp'],
            'greek': ['ell'],
            'turkish': ['tur'],
        }
        
        logger.info(f"✅ Universal OCR Processor initialized with {len(self.available_languages)} languages")
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """Universal OCR extraction with robust language detection"""
        start_time = time.time()
        
        try:
            # Step 1: Enhanced preprocessing
            processed_img, quality_info = await asyncio.wait_for(
                self._enhanced_preprocess(image_bytes),
                timeout=5.0
            )
            
            logger.info(f"🔍 Image quality: {quality_info['quality']} (blur: {quality_info['blur_score']:.1f})")
            
            # Step 2: Robust language detection
            detected_language, detection_confidence = await self._robust_language_detection(processed_img)
            logger.info(f"🎯 Detected language: {detected_language} (confidence: {detection_confidence:.2f})")
            
            # Step 3: Multi-strategy extraction based on detection confidence
            if detection_confidence > 0.6:
                # High confidence - use focused extraction
                extracted_text = await self._focused_extraction(processed_img, detected_language, quality_info)
            else:
                # Low confidence - try multiple strategies
                extracted_text = await self._multi_strategy_extraction(processed_img, quality_info)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_meaningful_text(extracted_text):
                cleaned_text = self._clean_extracted_text(extracted_text)
                logger.info(f"✅ OCR completed in {processing_time:.2f}s - {len(cleaned_text)} chars")
                return cleaned_text
            else:
                logger.warning("❌ No meaningful text extracted")
                return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _robust_language_detection(self, image: np.ndarray) -> Tuple[str, float]:
        """Robust language detection with multiple strategies"""
        loop = asyncio.get_event_loop()
        
        # Strategy 1: Quick multi-language detection
        multi_lang_result = await self._multi_language_detection(image, loop)
        if multi_lang_result and multi_lang_result['confidence'] > 0.7:
            return multi_lang_result['script'], multi_lang_result['confidence']
        
        # Strategy 2: Individual language sampling
        individual_result = await self._individual_language_sampling(image, loop)
        if individual_result and individual_result['confidence'] > 0.5:
            return individual_result['script'], individual_result['confidence']
        
        # Strategy 3: Script-based detection
        script_result = await self._script_based_detection(image, loop)
        if script_result:
            return script_result['script'], script_result['confidence']
        
        # Default fallback
        return 'latin', 0.3
    
    async def _multi_language_detection(self, image: np.ndarray, loop) -> dict:
        """Multi-language detection for common scripts"""
        multi_lang_groups = [
            ('eng+amh+ara', ['latin', 'ethiopic', 'arabic']),
            ('chi_sim+jpn+kor', ['chinese', 'japanese', 'korean']),
            ('rus+hin+heb', ['cyrillic', 'devanagari', 'hebrew']),
        ]
        
        for lang_group, scripts in multi_lang_groups:
            try:
                # Filter to available languages
                available_langs = '+'.join([lang for lang in lang_group.split('+') 
                                          if lang in self.available_languages])
                if not available_langs:
                    continue
                
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, available_langs, self.configs['quick_detect']
                )
                
                if text and len(text.strip()) > 10:
                    # Analyze which script dominates
                    best_script = self._analyze_dominant_script(text, scripts)
                    confidence = self._calculate_text_confidence(text)
                    
                    if confidence > 0.5:
                        logger.info(f"🔍 Multi-lang detected: {best_script} (confidence: {confidence:.2f})")
                        return {'script': best_script, 'confidence': confidence}
                        
            except Exception as e:
                logger.debug(f"Multi-lang detection failed: {e}")
                continue
        
        return None
    
    async def _individual_language_sampling(self, image: np.ndarray, loop) -> dict:
        """Individual language sampling with better text extraction"""
        language_tests = [
            ('amh', 'ethiopic'),
            ('ara', 'arabic'),
            ('chi_sim', 'chinese'),
            ('jpn', 'japanese'),
            ('kor', 'korean'),
            ('rus', 'cyrillic'),
            ('hin', 'devanagari'),
            ('eng', 'latin'),
        ]
        
        best_score = 0
        best_script = 'latin'
        
        for lang_code, script in language_tests:
            if lang_code not in self.available_languages:
                continue
                
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang_code, self.configs['document']  # Use document mode for better extraction
                )
                
                if text and len(text.strip()) > 15:  # Require more text for confidence
                    score = self._calculate_script_specific_confidence(text, script)
                    logger.info(f"🔍 {lang_code} sample: {len(text.strip())} chars (score: {score:.2f})")
                    
                    if score > best_score:
                        best_score = score
                        best_script = script
                        
            except Exception as e:
                logger.debug(f"Language sample {lang_code} failed: {e}")
                continue
        
        return {'script': best_script, 'confidence': best_score} if best_score > 0.3 else None
    
    async def _script_based_detection(self, image: np.ndarray, loop) -> dict:
        """Script-based detection using character analysis"""
        try:
            # Use English config but analyze characters
            text = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image, 'eng', self.configs['quick_detect']
            )
            
            if text and len(text.strip()) > 10:
                detected_script = self._detect_script_by_characters(text)
                confidence = self._calculate_text_confidence(text)
                return {'script': detected_script, 'confidence': confidence}
                
        except Exception as e:
            logger.debug(f"Script-based detection failed: {e}")
        
        return None
    
    def _analyze_dominant_script(self, text: str, possible_scripts: List[str]) -> str:
        """Analyze which script dominates the text"""
        script_scores = {}
        
        for script in possible_scripts:
            score = self._calculate_script_specific_confidence(text, script)
            script_scores[script] = score
        
        return max(script_scores.items(), key=lambda x: x[1])[0]
    
    def _detect_script_by_characters(self, text: str) -> str:
        """Detect script by analyzing character ranges"""
        clean_text = text.strip()
        
        # Count characters by script
        script_counts = {
            'ethiopic': sum(1 for c in clean_text if '\u1200' <= c <= '\u137F'),
            'arabic': sum(1 for c in clean_text if '\u0600' <= c <= '\u06FF'),
            'chinese': sum(1 for c in clean_text if '\u4e00' <= c <= '\u9fff'),
            'cyrillic': sum(1 for c in clean_text if '\u0400' <= c <= '\u04FF'),
            'devanagari': sum(1 for c in clean_text if '\u0900' <= c <= '\u097F'),
            'latin': sum(1 for c in clean_text if c.isalpha() and c.isascii()),
        }
        
        # Find dominant script
        dominant_script = max(script_counts.items(), key=lambda x: x[1])[0]
        
        # If no specific script characters found, default to latin
        if script_counts[dominant_script] == 0:
            return 'latin'
        
        return dominant_script
    
    def _calculate_script_specific_confidence(self, text: str, script: str) -> float:
        """Calculate confidence for specific script"""
        clean_text = text.strip()
        if not clean_text or len(clean_text) < 10:
            return 0.0
        
        base_score = 0.3
        
        # Length bonus
        length_bonus = min(len(clean_text) / 150, 0.4)
        base_score += length_bonus
        
        # Script-specific character detection with higher weights
        if script == 'ethiopic':
            ethiopic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137F')
            if ethiopic_chars > 0:
                base_score += min(ethiopic_chars / len(clean_text) * 0.8, 0.5)
        elif script == 'arabic':
            arabic_chars = sum(1 for c in clean_text if '\u0600' <= c <= '\u06FF')
            if arabic_chars > 0:
                base_score += min(arabic_chars / len(clean_text) * 0.8, 0.5)
        elif script in ['chinese', 'japanese']:
            cjk_chars = sum(1 for c in clean_text if '\u4e00' <= c <= '\u9fff')
            if cjk_chars > 0:
                base_score += min(cjk_chars / len(clean_text) * 0.8, 0.5)
        elif script == 'latin':
            latin_chars = sum(1 for c in clean_text if c.isalpha() and c.isascii())
            if latin_chars > 0:
                base_score += min(latin_chars / len(clean_text) * 0.6, 0.4)
        
        return min(1.0, base_score)
    
    async def _focused_extraction(self, image: np.ndarray, script: str, quality_info: dict) -> str:
        """Focused extraction for detected script"""
        loop = asyncio.get_event_loop()
        
        if quality_info['blur_score'] < 300:
            base_config = self.configs['blurry']
        else:
            base_config = self.configs['standard']
        
        script_languages = self.language_scripts.get(script, ['eng'])
        available_langs = [lang for lang in script_languages if lang in self.available_languages]
        
        if not available_langs:
            available_langs = ['eng']
        
        # Try different PSM modes for better extraction
        psm_modes = ['6', '3', '7']
        
        for psm in psm_modes:
            config = f"{base_config} --psm {psm}"
            lang_group = '+'.join(available_langs[:8])
            
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang_group, config
                )
                
                if text and self._is_meaningful_text(text):
                    logger.info(f"🎯 Focused {script} (PSM{psm}): {len(text.strip())} chars")
                    return text
                    
            except Exception as e:
                logger.debug(f"Focused {script} PSM{psm} failed: {e}")
                continue
        
        return ""
    
    async def _multi_strategy_extraction(self, image: np.ndarray, quality_info: dict) -> str:
        """Multi-strategy extraction for low confidence detection"""
        loop = asyncio.get_event_loop()
        
        if quality_info['blur_score'] < 300:
            base_config = self.configs['blurry']
        else:
            base_config = self.configs['standard']
        
        # Try comprehensive language groups
        comprehensive_groups = [
            'eng+amh+ara+fra+spa+deu+ita+por+rus',
            'chi_sim+chi_tra+jpn+kor',
            'hin+ben+tha+vie+heb+tur',
            'eng+amh',
            'eng'
        ]
        
        for lang_group in comprehensive_groups:
            try:
                available_langs = '+'.join([lang for lang in lang_group.split('+') 
                                          if lang in self.available_languages])
                if not available_langs:
                    continue
                
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, available_langs, base_config
                )
                
                if text and self._is_meaningful_text(text):
                    logger.info(f"🌐 Comprehensive {available_langs}: {len(text.strip())} chars")
                    return text
                    
            except Exception as e:
                logger.debug(f"Comprehensive {lang_group} failed: {e}")
                continue
        
        return ""
    
    def _calculate_text_confidence(self, text: str) -> float:
        """Calculate general text confidence"""
        clean_text = text.strip()
        if not clean_text:
            return 0.0
        
        score = 0.5
        score += min(len(clean_text) / 200, 0.3)
        
        words = clean_text.split()
        if len(words) >= 3:
            score += 0.2
        
        unique_ratio = len(set(clean_text)) / len(clean_text)
        if unique_ratio > 0.5:
            score += 0.1
        
        return min(1.0, score)
    
    def _is_meaningful_text(self, text: str) -> bool:
        """Check if text is meaningful"""
        if not text or len(text.strip()) < 10:
            return False
        
        clean_text = text.strip()
        
        # More permissive checks for different languages
        unique_chars = len(set(clean_text))
        if unique_chars < 3:
            return False
        
        words = clean_text.split()
        if len(words) < 2:
            return False
        
        # Allow longer words for languages like German, shorter for Chinese
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 1.0 or avg_word_length > 25:
            return False
        
        return True
    
    # Keep the same _enhanced_preprocess and _clean_extracted_text methods from previous version
    async def _enhanced_preprocess(self, image_bytes: bytes) -> Tuple[np.ndarray, dict]:
        """Enhanced preprocessing with quality analysis"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            contrast = gray.std()
            
            quality_info = {
                'blur_score': blur_score,
                'contrast': contrast,
                'quality': 'excellent' if blur_score > 2000 else 'good' if blur_score > 500 else 'poor' if blur_score > 100 else 'very_poor'
            }
            
            if blur_score < 300:
                logger.info("🔄 Applying advanced blurry image enhancement")
                denoised = cv2.medianBlur(gray, 3)
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(denoised, -1, kernel)
                alpha = 1.8
                beta = 20
                enhanced = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(enhanced)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
            
            height, width = enhanced.shape
            if max(height, width) > 1600:
                scale = 1600 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            return enhanced, quality_info
            
        except Exception as e:
            logger.error(f"Enhanced preprocessing failed: {e}")
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            img_array = np.array(image)
            quality_info = {'blur_score': 100, 'contrast': 50, 'quality': 'unknown'}
            return img_array, quality_info
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text"""
        if not text:
            return text
        
        cleaned = text.strip()
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
        cleaned = re.sub(r'^\s*[0-9ivx]+\s*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^\s*[^\w\s]+\s*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()

# Global instance
smart_ocr_processor = SmartOCRProcessor()