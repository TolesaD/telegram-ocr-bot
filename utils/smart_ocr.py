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
    """Universal OCR processor that handles all languages intelligently"""
    
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
        
        # Language scripts grouped by writing system - REORDERED for priority
        self.language_scripts = {
            'ethiopic': ['amh', 'tir', 'orm'],  # HIGHEST PRIORITY - Amharic first
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
            'latin': ['eng', 'fra', 'spa', 'deu', 'ita', 'por', 'nld', 'swe', 'dan', 'nor', 'fin', 'pol', 'ces', 'hun', 'ron', 'hrv', 'srp', 'slk', 'slv', 'lav', 'lit', 'est', 'lav', 'glg', 'cat', 'eus'],  # LOWEST PRIORITY
        }
        
        logger.info(f"✅ Universal OCR Processor initialized with {len(self.available_languages)} languages")
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """Universal OCR extraction that handles all languages intelligently"""
        start_time = time.time()
        
        try:
            # Step 1: Enhanced preprocessing
            processed_img, quality_info = await asyncio.wait_for(
                self._enhanced_preprocess(image_bytes),
                timeout=5.0
            )
            
            logger.info(f"🔍 Image quality: {quality_info['quality']} (blur: {quality_info['blur_score']:.1f})")
            
            # Step 2: Universal language extraction
            extracted_text = await asyncio.wait_for(
                self._universal_language_extraction(processed_img, quality_info),
                timeout=25.0
            )
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_meaningful_text(extracted_text):
                # Clean and format the text
                cleaned_text = self._clean_extracted_text(extracted_text)
                logger.info(f"✅ Universal OCR completed in {processing_time:.2f}s - {len(cleaned_text)} chars")
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
                # 1. Noise reduction
                denoised = cv2.medianBlur(gray, 3)
                
                # 2. Sharpening
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(denoised, -1, kernel)
                
                # 3. Contrast enhancement
                alpha = 1.8
                beta = 20
                enhanced = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
                
                # 4. CLAHE for local contrast
                clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(enhanced)
            else:
                # Normal enhancement for clear images
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(gray)
            
            # Resize if too large (better for OCR accuracy)
            height, width = enhanced.shape
            if max(height, width) > 1600:
                scale = 1600 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            return enhanced, quality_info
            
        except Exception as e:
            logger.error(f"Enhanced preprocessing failed: {e}")
            # Fallback to basic processing
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            img_array = np.array(image)
            quality_info = {'blur_score': 100, 'contrast': 50, 'quality': 'unknown'}
            return img_array, quality_info
    
    async def _universal_language_extraction(self, image: np.ndarray, quality_info: dict) -> str:
        """Universal language extraction that handles all writing systems"""
        loop = asyncio.get_event_loop()
        
        # Choose config based on image quality
        if quality_info['blur_score'] < 300:
            base_config = self.configs['blurry']
        else:
            base_config = self.configs['standard']
        
        # Strategy 1: Try script-based language groups (most effective)
        script_results = await self._try_script_based_extraction(image, base_config, loop)
        if script_results:
            best_result = self._select_best_script_result(script_results)
            if best_result['score'] > 0.7:  # High confidence
                logger.info(f"🏆 Script-based winner: {best_result['script']} (score: {best_result['score']:.2f})")
                return best_result['text']
        
        # Strategy 2: Try individual major languages
        individual_results = await self._try_individual_languages(image, base_config, loop)
        if individual_results:
            best_individual = max(individual_results, key=lambda x: x['score'])
            if best_individual['score'] > 0.6:
                logger.info(f"🔤 Individual winner: {best_individual['lang']} (score: {best_individual['score']:.2f})")
                return best_individual['text']
        
        # Strategy 3: Try auto-detection with different PSM modes
        auto_results = await self._try_auto_detection(image, loop)
        if auto_results:
            best_auto = max(auto_results, key=lambda x: x['score'])
            logger.info(f"🤖 Auto-detection winner: PSM{best_auto['psm']} (score: {best_auto['score']:.2f})")
            return best_auto['text']
        
        return ""
    
    def _select_best_script_result(self, script_results: List[dict]) -> dict:
        """Select the best script result with intelligent prioritization"""
        if not script_results:
            return None
        
        # Create script priority mapping (higher number = higher priority)
        script_priority = {
            'ethiopic': 100,    # Highest priority for Amharic
            'arabic': 90,
            'chinese': 85,
            'japanese': 85,
            'korean': 85,
            'devanagari': 80,
            'bengali': 80,
            'hebrew': 75,
            'thai': 70,
            'vietnamese': 70,
            'cyrillic': 60,
            'greek': 55,
            'turkish': 50,
            'latin': 10,        # Lowest priority - English/Latin as last resort
        }
        
        # Score each result with priority bonus
        scored_results = []
        for result in script_results:
            base_score = result['score']
            priority_bonus = script_priority.get(result['script'], 0) / 100.0
            final_score = base_score + priority_bonus
            
            scored_results.append({
                **result,
                'final_score': final_score,
                'priority_bonus': priority_bonus
            })
            
            logger.info(f"📊 {result['script']}: base={base_score:.2f}, priority_bonus={priority_bonus:.2f}, final={final_score:.2f}")
        
        # Select the best result
        best_result = max(scored_results, key=lambda x: x['final_score'])
        return best_result
    
    async def _try_script_based_extraction(self, image: np.ndarray, base_config: str, loop) -> List[dict]:
        """Try extraction by language script groups"""
        results = []
        
        for script_name, languages in self.language_scripts.items():
            # Filter to available languages only
            available_langs = [lang for lang in languages if lang in self.available_languages]
            if not available_langs:
                continue
                
            lang_group = '+'.join(available_langs[:8])  # Limit to 8 languages per group
            
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang_group, base_config
                )
                
                if text and self._is_meaningful_text(text):
                    confidence = self._calculate_text_confidence(text, script_name)
                    if confidence > 0.3:  # Minimum confidence threshold
                        # Calculate script-specific confidence
                        script_confidence = self._calculate_script_specific_confidence(text, script_name)
                        final_confidence = max(confidence, script_confidence)
                        
                        results.append({
                            'script': script_name,
                            'text': text,
                            'score': final_confidence,
                            'languages': available_langs
                        })
                        logger.info(f"📜 {script_name} script: {len(text.strip())} chars (score: {final_confidence:.2f})")
                        
            except Exception as e:
                logger.debug(f"Script {script_name} failed: {e}")
                continue
        
        return results
    
    def _calculate_script_specific_confidence(self, text: str, script_name: str) -> float:
        """Calculate confidence specific to script type"""
        clean_text = text.strip()
        if not clean_text:
            return 0.0
        
        base_score = 0.5
        
        # Script-specific character detection
        if script_name == 'ethiopic':
            # Count Amharic/Ethiopic characters
            ethiopic_chars = sum(1 for c in clean_text if '\u1200' <= c <= '\u137F')
            if ethiopic_chars > 0:
                ethiopic_ratio = ethiopic_chars / len(clean_text)
                base_score += min(ethiopic_ratio * 0.5, 0.3)  # Bonus for Ethiopic characters
                
        elif script_name == 'arabic':
            # Count Arabic characters
            arabic_chars = sum(1 for c in clean_text if '\u0600' <= c <= '\u06FF')
            if arabic_chars > 0:
                arabic_ratio = arabic_chars / len(clean_text)
                base_score += min(arabic_ratio * 0.5, 0.3)
                
        elif script_name == 'chinese' or script_name == 'japanese':
            # Count CJK characters
            cjk_chars = sum(1 for c in clean_text if '\u4e00' <= c <= '\u9fff')
            if cjk_chars > 0:
                cjk_ratio = cjk_chars / len(clean_text)
                base_score += min(cjk_ratio * 0.5, 0.3)
        
        return min(1.0, base_score)
    
    async def _try_individual_languages(self, image: np.ndarray, base_config: str, loop) -> List[dict]:
        """Try individual major languages"""
        results = []
        
        # Major languages to try individually - Amharic first
        major_languages = ['amh', 'ara', 'chi_sim', 'chi_tra', 'jpn', 'kor', 'rus', 'fra', 'spa', 'deu', 'ita', 'por', 'hin', 'ben', 'tur', 'heb', 'tha', 'vie', 'eng']  # English last
        
        for lang in major_languages:
            if lang not in self.available_languages:
                continue
                
            try:
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, lang, base_config
                )
                
                if text and self._is_meaningful_text(text):
                    confidence = self._calculate_text_confidence(text, 'individual')
                    if confidence > 0.4:
                        results.append({
                            'lang': lang,
                            'text': text,
                            'score': confidence
                        })
                        logger.info(f"🎯 Individual {lang}: {len(text.strip())} chars (score: {confidence:.2f})")
                        
            except Exception as e:
                logger.debug(f"Individual {lang} failed: {e}")
                continue
        
        return results
    
    async def _try_auto_detection(self, image: np.ndarray, loop) -> List[dict]:
        """Try auto-detection with different PSM modes"""
        results = []
        psm_modes = ['6', '3', '7', '8', '13']  # Different segmentation modes
        
        for psm in psm_modes:
            try:
                config = f"--oem 3 --psm {psm}"
                text = await loop.run_in_executor(
                    self.executor,
                    pytesseract.image_to_string,
                    image, 'eng', config  # Use English as base for auto-detection
                )
                
                if text and self._is_meaningful_text(text):
                    confidence = self._calculate_text_confidence(text, 'auto')
                    results.append({
                        'psm': psm,
                        'text': text,
                        'score': confidence
                    })
                    logger.info(f"🔧 Auto PSM{psm}: {len(text.strip())} chars (score: {confidence:.2f})")
                    
            except Exception as e:
                logger.debug(f"Auto PSM{psm} failed: {e}")
                continue
        
        return results
    
    def _calculate_text_confidence(self, text: str, method: str) -> float:
        """Calculate confidence score for extracted text"""
        clean_text = text.strip()
        if not clean_text:
            return 0.0
        
        # Base score from text quality
        score = 0.5
        
        # Length bonus (normalized)
        length_score = min(len(clean_text) / 200, 0.3)
        score += length_score
        
        # Word count bonus
        words = clean_text.split()
        if len(words) >= 3:
            score += 0.2
        
        # Character diversity bonus
        unique_ratio = len(set(clean_text)) / len(clean_text)
        if unique_ratio > 0.5:
            score += 0.1
        
        # Penalize excessive special characters
        special_chars = sum(1 for c in clean_text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(clean_text)
        if special_ratio > 0.3:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _is_meaningful_text(self, text: str) -> bool:
        """Check if text is meaningful and not garbage"""
        if not text or len(text.strip()) < 10:
            return False
        
        clean_text = text.strip()
        
        # Check character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 5:
            return False
        
        # Check word structure
        words = clean_text.split()
        if len(words) < 3:
            return False
        
        # Check for reasonable word lengths
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 1.5 or avg_word_length > 15:
            return False
        
        # Check for excessive special characters
        special_chars = sum(1 for c in clean_text if not c.isalnum() and not c.isspace())
        if special_chars > len(clean_text) * 0.4:
            return False
        
        # Check for repeated nonsense
        if len(clean_text) > 20:
            repeated_ratio = max(clean_text.count(c) for c in clean_text) / len(clean_text)
            if repeated_ratio > 0.6:
                return False
        
        return True
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text"""
        if not text:
            return text
        
        # Basic cleaning
        cleaned = text.strip()
        
        # Remove excessive line breaks (more than 2 consecutive)
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        # Remove leading/trailing whitespace from each line
        cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
        
        # Remove page numbers and common OCR artifacts
        cleaned = re.sub(r'^\s*[0-9ivx]+\s*$', '', cleaned, flags=re.MULTILINE)
        
        # Remove isolated special characters
        cleaned = re.sub(r'^\s*[^\w\s]+\s*$', '', cleaned, flags=re.MULTILINE)
        
        # Final cleanup of extra whitespace
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned.strip()

# Global instance
smart_ocr_processor = SmartOCRProcessor()