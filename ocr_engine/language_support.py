# ocr_engine/language_support.py
# Optimized language support with better detection and configurations

LANGUAGE_MAPPING = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese',
    'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic', 'hi': 'Hindi',
    'bn': 'Bengali', 'pa': 'Punjabi', 'gu': 'Gujarati', 'or': 'Odia',
    'ta': 'Tamil', 'te': 'Telugu', 'kn': 'Kannada', 'ml': 'Malayalam',
    'th': 'Thai', 'vi': 'Vietnamese', 'tr': 'Turkish', 'pl': 'Polish',
    'uk': 'Ukrainian', 'ro': 'Romanian', 'nl': 'Dutch', 'hu': 'Hungarian',
    'sv': 'Swedish', 'cs': 'Czech', 'el': 'Greek', 'he': 'Hebrew',
    'fa': 'Persian', 'ur': 'Urdu', 'am': 'Amharic', 'ti': 'Tigrinya',
    'so': 'Somali', 'sw': 'Swahili', 'yo': 'Yoruba', 'ig': 'Igbo',
    'ha': 'Hausa', 'af': 'Afrikaans', 'zu': 'Zulu', 'xh': 'Xhosa'
}

# Core languages with reliable Tesseract support
CORE_LANGUAGES = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar', 'hi', 'am']

TESSERACT_LANGUAGES = {
    'en': 'eng', 'es': 'spa', 'fr': 'fra', 'de': 'deu', 'it': 'ita',
    'pt': 'por', 'ru': 'rus', 'zh': 'chi_sim', 'ja': 'jpn', 'ko': 'kor',
    'ar': 'ara', 'hi': 'hin', 'bn': 'ben', 'pa': 'pan', 'gu': 'guj',
    'or': 'ori', 'ta': 'tam', 'te': 'tel', 'kn': 'kan', 'ml': 'mal',
    'th': 'tha', 'vi': 'vie', 'tr': 'tur', 'pl': 'pol', 'uk': 'ukr',
    'ro': 'ron', 'nl': 'nld', 'hu': 'hun', 'sv': 'swe', 'cs': 'ces',
    'el': 'ell', 'he': 'heb', 'fa': 'fas', 'ur': 'urd', 'am': 'amh',
    'ti': 'tir', 'so': 'som', 'sw': 'swa', 'yo': 'yor', 'ig': 'ibo',
    'ha': 'hau', 'af': 'afr', 'zu': 'zul', 'xh': 'xho'
}

# Script families for better processing
SCRIPT_FAMILIES = {
    'Latin': ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'sv', 'tr', 'vi', 'ro'],
    'Cyrillic': ['ru', 'uk', 'bg', 'sr'],
    'Arabic': ['ar', 'fa', 'ur'],
    'Devanagari': ['hi', 'ne', 'mr'],
    'Bengali': ['bn'],
    'Chinese': ['zh'],
    'Japanese': ['ja'],
    'Korean': ['ko'],
    'Ethiopic': ['am', 'ti'],
    'Thai': ['th'],
    'Hebrew': ['he'],
    'Greek': ['el'],
    'Tamil': ['ta'],
    'Telugu': ['te'],
    'Kannada': ['kn'],
    'Malayalam': ['ml']
}

def get_script_family(lang_code):
    """Get script family for language"""
    for script, languages in SCRIPT_FAMILIES.items():
        if lang_code in languages:
            return script
    return 'Latin'  # Default

def get_tesseract_code(lang_code):
    """Get Tesseract language code with fallback"""
    return TESSERACT_LANGUAGES.get(lang_code, 'eng')

def get_ocr_config(language, script_family, image_size=None):
    """Get optimized OCR configuration for language and script"""
    base_config = "--oem 3 --dpi 300 -c tessedit_do_invert=0"
    
    # Script-specific configurations
    script_configs = {
        'Latin': "--psm 6 -c preserve_interword_spaces=1",
        'Cyrillic': "--psm 6 -c textord_min_linesize=1.5",
        'Arabic': "--psm 6 -c textord_min_linesize=2.0 -c textord_old_baselines=1",
        'Chinese': "--psm 6 -c textord_min_linesize=2.5 -c textord_old_baselines=1",
        'Japanese': "--psm 6 -c textord_min_linesize=2.5",
        'Korean': "--psm 6 -c textord_min_linesize=2.0",
        'Ethiopic': "--psm 6 -c textord_min_linesize=1.8 -c textord_old_baselines=1",
        'Thai': "--psm 6 -c textord_min_linesize=2.0",
        'Devanagari': "--psm 6 -c textord_min_linesize=2.0"
    }
    
    config = f"{base_config} {script_configs.get(script_family, '--psm 6')}"
    
    # Adjust for image size
    if image_size and image_size[0] * image_size[1] > 2000000:  # Large images
        config = config.replace("--psm 6", "--psm 4")
    elif image_size and image_size[0] * image_size[1] < 100000:  # Small images
        config = config.replace("--psm 6", "--psm 8")
    
    return config

def detect_script_from_text(text):
    """Detect script from text content with improved accuracy"""
    if not text:
        return 'Latin'
    
    # Count characters by script ranges
    script_counts = {
        'Latin': sum(1 for c in text if c.isascii() and c.isalpha()),
        'Cyrillic': sum(1 for c in text if '\u0400' <= c <= '\u04FF'),
        'Arabic': sum(1 for c in text if '\u0600' <= c <= '\u06FF'),
        'Devanagari': sum(1 for c in text if '\u0900' <= c <= '\u097F'),
        'Chinese': sum(1 for c in text if '\u4E00' <= c <= '\u9FFF'),
        'Japanese': sum(1 for c in text if ('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF')),
        'Korean': sum(1 for c in text if '\uAC00' <= c <= '\uD7A3'),
        'Ethiopic': sum(1 for c in text if '\u1200' <= c <= '\u137F'),
        'Thai': sum(1 for c in text if '\u0E00' <= c <= '\u0E7F'),
        'Hebrew': sum(1 for c in text if '\u0590' <= c <= '\u05FF')
    }
    
    # Return script with highest count
    return max(script_counts.items(), key=lambda x: x[1])[0]

def is_amharic_character(char):
    """Check if character is Amharic/Ethiopic"""
    return '\u1200' <= char <= '\u137F'

def validate_ocr_result(text, expected_language):
    """Validate OCR result quality"""
    if not text or len(text.strip()) < 3:
        return False, "Text too short"
    
    # Check character diversity
    unique_chars = len(set(text))
    if unique_chars < 2:
        return False, "Low character diversity"
    
    # Language-specific validation
    if expected_language == 'am':
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        if amharic_chars < 2:
            return False, "No Amharic characters detected"
    
    return True, "Valid"

def get_fallback_languages(primary_lang):
    """Get fallback languages for OCR"""
    script_family = get_script_family(primary_lang)
    fallbacks = {
        'Latin': ['eng', 'spa', 'fra'],
        'Cyrillic': ['rus', 'ukr'],
        'Arabic': ['ara', 'fas'],
        'Chinese': ['chi_sim', 'chi_tra'],
        'Japanese': ['jpn'],
        'Korean': ['kor'],
        'Ethiopic': ['amh'],
        'Devanagari': ['hin', 'nep']
    }
    return fallbacks.get(script_family, ['eng'])

def clean_ocr_text(text, language):
    """Clean OCR text based on language"""
    if not text:
        return ""
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remove lines that are mostly garbage
        if is_garbage_line(line, language):
            continue
            
        cleaned_lines.append(line)
    
    # Remove duplicate consecutive lines
    unique_lines = []
    for i, line in enumerate(cleaned_lines):
        if i == 0 or line != cleaned_lines[i-1]:
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def is_garbage_line(line, language):
    """Check if line is likely garbage"""
    if len(line) < 2:
        return True
    
    # Count meaningful characters
    if language == 'am':
        meaningful_chars = sum(1 for c in line if is_amharic_character(c) or c.isalnum())
    else:
        meaningful_chars = sum(1 for c in line if c.isalnum())
    
    # If less than 40% meaningful, consider garbage
    return (meaningful_chars / len(line)) < 0.4