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
    """Universal OCR processor with balanced language detection"""
    
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
            'blurry': '--oem 3 --psm 6 -c textord_old_baselines=1'
        }
        
        # Language scripts grouped by writing system - BALANCED PRIORITY
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
        """Universal OCR extraction with balanced language detection"""
        start_time = time.time()
        
        try:
            # Step 1: Enhanced preprocessing
            processed_img, quality_info = await asyncio.wait_for(
                self._enhanced_preprocess(image_bytes),
                timeout=5.0
            )
            
            logger.info(f"🔍 Image quality: {quality_info['quality']} (blur: {quality_info['blur_score']:.1f})")
            
            # Step 2: Smart language detection first
            detected_language = await self._smart_language_detection(processed_img, quality_info)
            logger.info(f"🎯 Detected primary language: {detected_language}")
            
            # Step 3: Extract with detected language focus
            extracted_text = await asyncio.wait_for(
                self._focused_language_extraction(processed_img, detected_language, quality_info),
                timeout=20.0
            )
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_reasonable_text(extracted_text):
                # Clean and format the text
                cleaned_text = self._clean_extracted_text(extracted_text)
                logger.info(f"✅ OCR completed in {processing_time:.2f}s - {len(cleaned_text)} chars")
                return cleaned_text
            else:
                # Final universal fallback
                logger.info("🔄 Trying universal fallback...")
                fallback_text = await self._universal_fallback(processed_img, quality_info)
                if fallback_text and self._is_reasonable_text(fallback_text):
                    logger.info(f"✅ Fallback completed in {processing_time:.2f}s")
                    return fallback_text
                else:
                    logger.warning("❌ No reasonable text extracted")
                    return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            logger.warning("OCR processing timeout")
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _smart_language_detection(self, image: np.ndarray, quality_info: dict) -> str:
        """Smart language detection using quick sampling"""
        loop = asyncio.get_event_loop()
        
        # Quick tests for major language families
        language_quick_tests = [
            ('eng', 'latin'),
            ('amh', 'ethiopic'), 
            ('ara', 'arabic'),
            ('chi_sim', 'chinese'),
            ('jpn', 'japanese'),
            ('kor', 'korean'),
            ('rus', 'cyrillic'),
            ('hin', 'devanagari'),
        ]
        
        best_lang = 'latin'  # Default fallback
        best_score = 0
        
        for lang_code, script in language_quick_tests:
            if lang_code not in self.available_languages:
                continue
                
            try:
                # Quick extraction with small timeout
                text = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        pytesseract.image_to_string,
                        image, lang_code, self.configs['single_line']
                    ),
                    timeout=2.0
                )
                
                if text:
                    score = self._calculate_language_confidence(text, script)
                    logger.info(f"🔍 Quick test {lang_code}: {len(text.strip())} chars (score: {score:.2f})")
                    
                    if score > best_score:
                        best_score = score
                        best_lang = script
                        
            except (asyncio.TimeoutError, Exception):
                continue
        
        return best_lang
    
    async def _focused_language_extraction(self, image: np.ndarray, primary_script: str, quality_info: dict) -> str:
        """Focused extraction based on detected language"""
        loop = asyncio.get_event_loop()
        
        # Choose config based on image quality
        if quality_info['blur_score'] < 300:
            base_config = self.configs['blurry']
        else:
            base_config = self.configs['standard']
        
        # Get languages for the detected script
        script_languages = self.language_scripts.get(primary_script, ['eng'])
        available_langs = [lang for lang in script_languages if lang in self.available_languages]
        
        if not available_langs:
            available_langs = ['eng']  # Fallback to English
        
        # Try script-specific extraction first
        lang_group = '+'.join(available_langs[:6])  # Limit languages per group
        
        try:
            text = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image, lang_group, base_config
            )
            
            if text and self._is_reasonable_text(text):
                logger.info(f"🎯 Focused {primary_script}: {len(text.strip())} chars")
                return text
        except Exception as e:
            logger.debug(f"Focused {primary_script} failed: {e}")
        
        return ""
    
    async def _universal_fallback(self, image: np.ndarray, quality_info: dict) -> str:
        """Universal fallback for all languages"""
        loop = asyncio.get_event_loop()
        
        if quality_info['blur_score'] < 300:
            base_config = self.configs['blurry']
        else:
            base_config = self.configs['standard']
        
        # Try major language combinations
        fallback_groups = [
            'eng+amh+ara+fra+spa+deu+ita+por+rus',  # Major languages
            'chi_sim+jpn+kor+hin',  # Asian languages
            'eng+amh',  # English + Amharic
            'eng',  # English only
        ]
        
        for lang_group in fallback_groups:
            try:
                # Filter to available languages
                available_langs = '+'.join([lang for lang in lang_group.split('+') 
                                          if lang in self.available_languages])
                if not available_langs:
                    continue
                    
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, available_langs, base_config
                )
                
                if text and self._is_reasonable_text(text):
                    logger.info(f"🔄 Fallback {available_langs}: {len(text.strip())} chars")
                    return text
                    
            except Exception as e:
                logger.debug(f"Fallback {lang_group} failed: {e}")
                continue
        
        return ""
    
    def _calculate_language_confidence(self, text: str, script: str) -> float:
        """Calculate confidence for specific script"""
        clean_text = text.strip()
        if not clean_text or len(clean_text) < 5:
            return 0.0
        
        base_score = 0.3
        
        # Length bonus
        length_bonus = min(len(clean_text) / 100, 0.3)
        base_score += length_bonus
        
        # Script-specific character detection
        if script == 'ethiopic':
            ethiopic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137F')
            if ethiopic_chars > 0:
                base_score += min(ethiopic_chars / len(clean_text), 0.4)
        elif script == 'latin':
            latin_chars = sum(1 for c in clean_text if c.isalpha() and c.isascii())
            if latin_chars > 0:
                base_score += min(latin_chars / len(clean_text), 0.3)
        elif script == 'arabic':
            arabic_chars = sum(1 for c in clean_text if '\u0600' <= c <= '\u06FF')
            if arabic_chars > 0:
                base_score += min(arabic_chars / len(clean_text), 0.4)
        elif script in ['chinese', 'japanese']:
            cjk_chars = sum(1 for c in clean_text if '\u4e00' <= c <= '\u9fff')
            if cjk_chars > 0:
                base_score += min(cjk_chars / len(clean_text), 0.4)
        
        return min(1.0, base_score)
    
    async def _enhanced_preprocess(self, image_bytes: bytes) -> Tuple[np.ndarray, dict]:
        """Enhanced preprocessing with quality analysis"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Quality analysis
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            contrast = gray.std()
            
            quality_info = {
                'blur_score': blur_score,
                'contrast': contrast,
                'quality': 'excellent' if blur_score > 2000 else 'good' if blur_score > 500 else 'poor' if blur_score > 100 else 'very_poor'
            }
            
            # Enhanced processing based on quality
            if blur_score < 300:  # Blurry image
                logger.info("🔄 Applying advanced blurry image enhancement")
                
                # Multiple enhancement techniques
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
            
            # Resize if too large
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
    
    def _is_reasonable_text(self, text: str) -> bool:
        """More permissive text validation"""
        if not text or len(text.strip()) < 8:
            return False
        
        clean_text = text.strip()
        
        # Basic character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 3:
            return False
        
        # Word structure check
        words = clean_text.split()
        if len(words) < 2:
            return False
        
        # Reasonable word lengths
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 1.2 or avg_word_length > 20:
            return False
        
        # Not excessive special characters
        special_chars = sum(1 for c in clean_text if not c.isalnum() and not c.isspace())
        if special_chars > len(clean_text) * 0.5:  # More permissive threshold
            return False
        
        return True
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text"""
        if not text:
            return text
        
        cleaned = text.strip()
        
        # Remove excessive line breaks
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        # Clean each line
        cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
        
        # Remove common OCR artifacts
        cleaned = re.sub(r'^\s*[0-9ivx]+\s*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'^\s*[^\w\s]+\s*$', '', cleaned, flags=re.MULTILINE)
        
        # Final whitespace cleanup
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()

# Global instance
smart_ocr_processor = SmartOCRProcessor()