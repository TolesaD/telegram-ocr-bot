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
    """ADVANCED OCR processor - Enhanced for blurry images and global languages"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.available_languages = self._get_available_languages()
        self.setup_ocr_configs()
        logger.info(f"✅ ADVANCED OCR Processor ready with {len(self.available_languages)} languages")
        
    def _get_available_languages(self) -> List[str]:
        """Get available languages from system"""
        try:
            langs = pytesseract.get_languages()
            logger.info(f"🌍 Available languages: {len(langs)}")
            return langs
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return ['eng', 'amh', 'ara', 'chi_sim', 'jpn', 'kor', 'rus', 'hin', 'spa', 'fra', 'deu']
    
    def setup_ocr_configs(self):
        """Enhanced OCR configurations for better accuracy"""
        self.configs = {
            'standard': '--oem 3 --psm 6 -c preserve_interword_spaces=1 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼ሀሁሂሃሄህሆለሉሊላሌልሎሏሐሑሒሓሔሕሖሗመሙሚማሜምሞሟመሙሚማሜምሞሟሠሡሢሣሤሥሦሧረሩሪራሬርሮሯሰሱሲሳሴስሶሷሸሹሺሻሼሽሾሿቀቁቂቃቄቅቆቇቈቊቋቌቍበቡቢባቤብቦቧቨቩቪቫቬቭቮቯተቱቲታቴትቶቷቸቹቺቻቼችቾቿኀኁኂኃኄኅኆኇኈኊኋኌኍነኑኒናኔንኖኗኘኙኚኛኜኝኞኟአኡኢኣኤእኦኧከኩኪካኬክኮኯኰኲኳኴኵኸኹኺኻኼኽኾወዉዊዋዌውዎዏዐዑዒዓዔዕዖዘዙዚዛዜዝዞዟዠዡዢዣዤዥዦዧየዩዪያዬይዮዯደዱዲዳዴድዶዷዸዹዺዻዼዽዾዿጀጁጂጃጄጅጆጇገጉጊጋጌግጎጏጐጒጓጔጕጠጡጢጣጤጥጦጧጨጩጪጫጬጭጮጯጰጱጲጳጴጵጶጷጸጹጺጻጼጽጾጿፀፁፂፃፄፅፆፇፈፉፊፋፌፍፎፏፐፑፒፓፔፕፖፗ',
            'document': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
            'single_line': '--oem 3 --psm 7',
            'single_word': '--oem 3 --psm 8',
        }
    
    async def extract_text_smart(self, image_bytes: bytes) -> str:
        """ADVANCED OCR extraction - Enhanced for blurry images"""
        start_time = time.time()
        
        try:
            # Step 1: Advanced preprocessing for blurry images
            processed_imgs = await self._advanced_preprocess(image_bytes)
            
            # Step 2: Multi-strategy extraction
            extracted_text = await self._multi_strategy_extraction(processed_imgs)
            
            processing_time = time.time() - start_time
            
            if extracted_text and self._is_good_text(extracted_text):
                logger.info(f"✅ ADVANCED OCR completed in {processing_time:.2f}s - {len(extracted_text)} chars")
                return extracted_text
            else:
                return "No readable text found. Please ensure the image contains clear, focused text."
                
        except asyncio.TimeoutError:
            return "Processing took too long. Please try a smaller or clearer image."
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return "Error processing image. Please try again with a different image."
    
    async def _advanced_preprocess(self, image_bytes: bytes) -> Dict[str, np.ndarray]:
        """Advanced preprocessing optimized for blurry images"""
        processed_images = {}
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("Failed to decode image")
            
            # Original grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            processed_images['original'] = gray
            
            # Strategy 1: CLAHE for contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            clahe_img = clahe.apply(gray)
            processed_images['clahe'] = clahe_img
            
            # Strategy 2: Unsharp masking for blurry images
            gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
            unsharp = cv2.addWeighted(gray, 2.0, gaussian, -1.0, 0)
            processed_images['unsharp'] = unsharp
            
            # Strategy 3: Bilateral filter for noise reduction while preserving edges
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            processed_images['bilateral'] = bilateral
            
            # Strategy 4: Morphological operations for text enhancement
            kernel = np.ones((1, 1), np.uint8)
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            processed_images['morph'] = morph
            
            # Strategy 5: Adaptive threshold for varying lighting
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            processed_images['adaptive'] = adaptive
            
            # Strategy 6: Resize for small/blurry text
            height, width = gray.shape
            if height < 500 or width < 500:
                scale_factor = 2.0
                resized = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
                processed_images['resized'] = resized
            
            logger.info(f"✅ Generated {len(processed_images)} preprocessing variations")
            
        except Exception as e:
            logger.error(f"Advanced preprocessing failed: {e}")
            # Fallback to basic processing
            image = Image.open(io.BytesIO(image_bytes)).convert('L')
            processed_images['fallback'] = np.array(image)
        
        return processed_images
    
    async def _multi_strategy_extraction(self, processed_images: Dict[str, np.ndarray]) -> str:
        """Multi-strategy extraction with voting system"""
        loop = asyncio.get_event_loop()
        all_results = []
        
        # Define language strategies
        language_strategies = [
            self._get_universal_language_group(),
            'eng+amh+ara',
            'eng+amh',
            'eng',
            'amh',
            'ara',
            'chi_sim',
            'jpn',
            'kor',
            'rus',
        ]
        
        # Try each preprocessing method with each language strategy
        for img_name, image in processed_images.items():
            for lang_group in language_strategies:
                if not lang_group:
                    continue
                    
                try:
                    # Try different PSM modes for different image types
                    psm_modes = ['6', '3', '7', '8'] if img_name in ['original', 'clahe'] else ['6', '7']
                    
                    for psm in psm_modes:
                        config = f'--oem 3 --psm {psm} -c preserve_interword_spaces=1'
                        
                        text = await loop.run_in_executor(
                            self.executor,
                            pytesseract.image_to_string,
                            image, lang_group, config
                        )
                        
                        if text and self._is_good_text(text):
                            logger.info(f"✅ Strategy success: {img_name} + {lang_group} + PSM{psm} - {len(text.strip())} chars")
                            all_results.append(text.strip())
                            
                except Exception as e:
                    logger.debug(f"Strategy {img_name}+{lang_group} failed: {e}")
                    continue
        
        # If we have results, use voting system to pick the best one
        if all_results:
            return self._select_best_result(all_results)
        
        return ""
    
    def _select_best_result(self, results: List[str]) -> str:
        """Select the best result from multiple OCR attempts"""
        if not results:
            return ""
        
        # Remove duplicates and similar results
        unique_results = list(set(results))
        
        # Score each result based on quality metrics
        scored_results = []
        for result in unique_results:
            score = self._score_text_quality(result)
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return the highest scored result
        best_score, best_result = scored_results[0]
        
        logger.info(f"🏆 Selected best result with score {best_score}: {len(best_result)} chars")
        return best_result
    
    def _score_text_quality(self, text: str) -> float:
        """Score text quality based on multiple factors"""
        if not text:
            return 0.0
        
        clean_text = text.strip()
        score = 0.0
        
        # Length factor (optimal length range)
        text_length = len(clean_text)
        if 20 <= text_length <= 5000:
            score += 0.3
        elif text_length > 5000:
            score += 0.2
        else:
            score += 0.1
        
        # Character diversity
        unique_chars = len(set(clean_text))
        diversity_ratio = unique_chars / text_length if text_length > 0 else 0
        if diversity_ratio > 0.4:
            score += 0.3
        elif diversity_ratio > 0.2:
            score += 0.2
        else:
            score += 0.1
        
        # Line structure
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        
        if 10 <= avg_line_length <= 100:
            score += 0.2
        elif avg_line_length > 0:
            score += 0.1
        
        # Word-like patterns
        words = re.findall(r'\b\w+\b', clean_text)
        if len(words) >= 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_universal_language_group(self) -> str:
        """Create an optimized universal language group"""
        # Priority languages for global coverage
        priority_languages = [
            'eng',    # English
            'amh',    # Amharic
            'ara',    # Arabic
            'chi_sim', # Chinese Simplified
            'jpn',    # Japanese  
            'kor',    # Korean
            'rus',    # Russian
            'hin',    # Hindi
            'spa',    # Spanish
            'fra',    # French
            'deu',    # German
            'ita',    # Italian
            'por',    # Portuguese
            'tur',    # Turkish
            'vie',    # Vietnamese
            'tha',    # Thai
        ]
        
        # Filter to available languages only
        available = [lang for lang in priority_languages if lang in self.available_languages]
        
        if not available:
            return 'eng'
        
        # Return combination of available languages (limit for performance)
        return '+'.join(available[:10])
    
    def _is_good_text(self, text: str) -> bool:
        """Enhanced text validation"""
        if not text:
            return False
        
        clean_text = text.strip()
        
        # Basic length check
        if len(clean_text) < 5:  # Reduced minimum for short texts
            return False
        
        # Check for character diversity
        unique_chars = len(set(clean_text))
        if unique_chars < 3:
            return False
        
        # Check for reasonable structure
        lines = clean_text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if len(non_empty_lines) < 1:
            return False
        
        # Enhanced garbage detection
        if len(clean_text) > 15:
            # Check for excessive repetition
            char_counts = {}
            for char in clean_text:
                if char.isalnum() or char.isspace():
                    char_counts[char] = char_counts.get(char, 0) + 1
            
            if char_counts:
                max_count = max(char_counts.values())
                if max_count / len(clean_text) > 0.6:  # 60% same character
                    return False
            
            # Check for too many special characters
            alpha_chars = sum(1 for c in clean_text if c.isalpha())
            digit_chars = sum(1 for c in clean_text if c.isdigit())
            total_chars = len(clean_text)
            
            if (alpha_chars + digit_chars) / total_chars < 0.4:  # At least 40% alphanumeric
                return False
        
        return True

# Global instance
smart_ocr_processor = SmartOCRProcessor()