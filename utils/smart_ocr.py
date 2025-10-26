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
    """Universal OCR processor with smart script selection"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.available_languages = self._get_available_languages()
        self.setup_ocr_configs()
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)} languages")
            major_langs = ['eng', 'amh', 'ara', 'chi_sim', 'chi_tra', 'jpn', 'kor', 'rus', 'hin', 'ben', 'heb', 'tha']
            available_major = [lang for lang in major_langs if lang in langs]
            logger.info(f"🔤 Available major languages: {available_major}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng', 'amh']
    
    def setup_ocr_configs(self):
        """Optimized OCR configurations for all scripts"""
        self.configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7 -c preserve_interword_spaces=1',
            'sparse_text': '--oem 3 --psm 6 -c textord_min_linesize=0.5',
            'blurry': '--oem 3 --psm 6 -c textord_old_baselines=1',
        }
        
        # Major script groups with dynamic priority
        self.major_scripts = [
            {
                'name': 'latin',
                'languages': ['eng', 'fra', 'spa', 'deu', 'ita', 'por', 'nld'],
                'test_lang': 'eng',
                'char_ranges': [('a', 'z'), ('A', 'Z')],
                'min_chars': 5,
                'base_priority': 50  # Balanced priority
            },
            {
                'name': 'ethiopic',
                'languages': ['amh', 'tir', 'orm'],
                'test_lang': 'amh',
                'char_ranges': [('\u1200', '\u137f')],
                'min_chars': 2,  # Fewer characters needed
                'base_priority': 80  # Higher priority for Ethiopic
            },
            {
                'name': 'chinese',
                'languages': ['chi_sim', 'chi_tra'],
                'test_lang': 'chi_sim',
                'char_ranges': [('\u4e00', '\u9fff')],
                'min_chars': 2,
                'base_priority': 70
            },
            {
                'name': 'japanese',
                'languages': ['jpn'],
                'test_lang': 'jpn', 
                'char_ranges': [('\u3040', '\u309f'), ('\u30a0', '\u30ff')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'korean',
                'languages': ['kor'],
                'test_lang': 'kor',
                'char_ranges': [('\uac00', '\ud7af')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'arabic',
                'languages': ['ara', 'fas', 'urd'],
                'test_lang': 'ara',
                'char_ranges': [('\u0600', '\u06ff')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'devanagari',
                'languages': ['hin', 'nep', 'mar'],
                'test_lang': 'hin',
                'char_ranges': [('\u0900', '\u097f')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'bengali',
                'languages': ['ben'],
                'test_lang': 'ben',
                'char_ranges': [('\u0980', '\u09ff')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'hebrew',
                'languages': ['heb'],
                'test_lang': 'heb',
                'char_ranges': [('\u0590', '\u05ff')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'thai',
                'languages': ['tha'],
                'test_lang': 'tha',
                'char_ranges': [('\u0e00', '\u0e7f')],
                'min_chars': 3,
                'base_priority': 70
            },
            {
                'name': 'cyrillic',
                'languages': ['rus', 'ukr', 'bul'],
                'test_lang': 'rus',
                'char_ranges': [('\u0400', '\u04ff')],
                'min_chars': 3,
                'base_priority': 70
            },
        ]
        
        logger.info(f"✅ Universal OCR Processor initialized with {len(self.available_languages)} languages")
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """Universal OCR extraction with smart script selection"""
        start_time = time.time()
        
        try:
            # Step 1: Enhanced preprocessing
            processed_img, quality_info = await asyncio.wait_for(
                self._enhanced_preprocess(image_bytes),
                timeout=5.0
            )
            
            logger.info(f"🔍 Image quality: {quality_info['quality']} (blur: {quality_info['blur_score']:.1f})")
            
            # Step 2: Smart script detection with dominance analysis
            best_script, extraction_text = await asyncio.wait_for(
                self._smart_script_detection(processed_img, quality_info),
                timeout=15.0
            )
            
            processing_time = time.time() - start_time
            
            if extraction_text and self._is_meaningful_text(extraction_text):
                cleaned_text = self._clean_extracted_text(extraction_text)
                logger.info(f"✅ {best_script} OCR completed in {processing_time:.2f}s - {len(cleaned_text)} chars")
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
    
    async def _smart_script_detection(self, image: np.ndarray, quality_info: dict) -> Tuple[str, str]:
        """Smart script detection that analyzes script dominance"""
        loop = asyncio.get_event_loop()
        
        if quality_info['blur_score'] < 300:
            base_config = self.configs['blurry']
        else:
            base_config = self.configs['standard']
        
        # Test all available scripts in parallel
        detection_tasks = []
        for script_info in self.major_scripts:
            if script_info['test_lang'] in self.available_languages:
                task = self._test_script_dominance(image, script_info, base_config, loop)
                detection_tasks.append(task)
        
        results = await asyncio.gather(*detection_tasks, return_exceptions=True)
        
        # Analyze results
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result.get('text') and self._is_meaningful_text(result['text']):
                valid_results.append(result)
        
        if not valid_results:
            return "unknown", ""
        
        # Find the most dominant script based on character analysis
        best_result = self._select_most_dominant_script(valid_results)
        return best_result['script'], best_result['text']
    
    async def _test_script_dominance(self, image: np.ndarray, script_info: dict, base_config: str, loop) -> dict:
        """Test a script and analyze its dominance in the extracted text"""
        try:
            # Use the script's languages for extraction
            languages = [lang for lang in script_info['languages'] if lang in self.available_languages]
            if not languages:
                return {'script': script_info['name'], 'confidence': 0.0, 'text': ''}
            
            lang_group = '+'.join(languages[:4])
            
            text = await loop.run_in_executor(
                self.executor,
                pytesseract.image_to_string,
                image, lang_group, base_config
            )
            
            if text and len(text.strip()) > 10:
                # Calculate dominance score
                dominance_score = self._calculate_script_dominance(text, script_info)
                
                if dominance_score > 0.3:  # Reasonable threshold
                    logger.info(f"📊 {script_info['name']}: {len(text.strip())} chars (dominance: {dominance_score:.2f})")
                    return {
                        'script': script_info['name'],
                        'confidence': dominance_score,
                        'text': text,
                        'dominance': dominance_score
                    }
                    
        except Exception as e:
            logger.debug(f"Script test {script_info['name']} failed: {e}")
        
        return {'script': script_info['name'], 'confidence': 0.0, 'text': '', 'dominance': 0.0}
    
    def _calculate_script_dominance(self, text: str, script_info: dict) -> float:
        """Calculate how dominant a script is in the text"""
        clean_text = text.strip()
        if not clean_text:
            return 0.0
        
        total_chars = len(clean_text)
        if total_chars < 10:
            return 0.0
        
        # Count script-specific characters
        script_chars = 0
        for char_range in script_info['char_ranges']:
            char_start, char_end = char_range
            if script_info['name'] == 'latin':
                # For Latin, only count ASCII letters
                range_chars = sum(1 for c in clean_text if char_start <= c.lower() <= char_end)
            else:
                # For other scripts, count characters in Unicode range
                range_chars = sum(1 for c in clean_text if char_start <= c <= char_end)
            script_chars += range_chars
        
        # Calculate dominance ratio
        dominance_ratio = script_chars / total_chars
        
        # Apply minimum character requirement
        if script_chars < script_info.get('min_chars', 3):
            return 0.0
        
        # Base score from dominance ratio
        base_score = dominance_ratio
        
        # Bonus for high dominance
        if dominance_ratio > 0.7:
            base_score += 0.2
        elif dominance_ratio > 0.5:
            base_score += 0.1
        
        # Bonus for script priority (small influence)
        priority_bonus = script_info.get('base_priority', 50) / 500.0  # Very small bonus
        base_score += priority_bonus
        
        # Special case: if Ethiopic has any characters and good ratio, boost it
        if script_info['name'] == 'ethiopic' and script_chars > 0 and dominance_ratio > 0.3:
            base_score += 0.15
        
        return min(1.0, base_score)
    
    def _select_most_dominant_script(self, results: List[dict]) -> dict:
        """Select the script with the highest dominance score"""
        if not results:
            return None
        
        # Sort by dominance score
        results.sort(key=lambda x: x.get('dominance', 0), reverse=True)
        
        top_result = results[0]
        top_dominance = top_result.get('dominance', 0)
        
        # Log the top candidates
        top_candidates = [f"{r['script']}({r.get('dominance', 0):.2f})" for r in results[:3]]
        logger.info(f"🏆 Top scripts: {top_candidates}")
        
        # If we have a clear winner (dominance > 0.5), use it
        if top_dominance > 0.5:
            logger.info(f"🎯 Clear winner: {top_result['script']} (dominance: {top_dominance:.2f})")
            return top_result
        
        # If multiple scripts have similar scores, use additional logic
        if len(results) > 1:
            second_dominance = results[1].get('dominance', 0)
            
            # If top two are close, prefer non-Latin scripts for diversity
            if abs(top_dominance - second_dominance) < 0.1:
                non_latin_results = [r for r in results if r['script'] != 'latin']
                if non_latin_results:
                    best_non_latin = max(non_latin_results, key=lambda x: x.get('dominance', 0))
                    if best_non_latin.get('dominance', 0) > 0.3:
                        logger.info(f"🔄 Preferring non-Latin: {best_non_latin['script']}")
                        return best_non_latin
        
        logger.info(f"🎯 Selected: {top_result['script']} (dominance: {top_dominance:.2f})")
        return top_result
    
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
    
    def _is_meaningful_text(self, text: str) -> bool:
        """Check if text is meaningful"""
        if not text or len(text.strip()) < 10:
            return False
        
        clean_text = text.strip()
        unique_chars = len(set(clean_text))
        if unique_chars < 3:
            return False
        
        words = clean_text.split()
        if len(words) < 2:
            return False
        
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 0.8 or avg_word_length > 30:
            return False
        
        return True
    
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