# ocr_engine/language_support.py
import logging

logger = logging.getLogger(__name__)

def get_tesseract_code(language: str) -> str:
    """Convert language code to Tesseract code"""
    mapping = {
        'en': 'eng', 'eng': 'eng', 'english': 'eng',
        'am': 'amh', 'amh': 'amh', 'amharic': 'amh',
        'ar': 'ara', 'ara': 'ara', 'arabic': 'ara',
        'zh': 'chi_sim', 'chi_sim': 'chi_sim', 'chinese': 'chi_sim',
        'ja': 'jpn', 'jpn': 'jpn', 'japanese': 'jpn',
        'ko': 'kor', 'kor': 'kor', 'korean': 'kor',
        'es': 'spa', 'spa': 'spa', 'spanish': 'spa',
        'fr': 'fra', 'fra': 'fra', 'french': 'fra',
        'de': 'deu', 'deu': 'deu', 'german': 'deu',
        'ru': 'rus', 'rus': 'rus', 'russian': 'rus'
    }
    return mapping.get(language.lower(), 'eng')

def get_amharic_config() -> str:
    """Get optimized Tesseract config for Amharic"""
    return '--oem 1 --psm 6 -c preserve_interword_spaces=1'

def is_amharic_character(char: str) -> bool:
    """Check if character is in Amharic Unicode range"""
    return '\u1200' <= char <= '\u137F'