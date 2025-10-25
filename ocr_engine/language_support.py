# ocr_engine/language_support.py
# Universal language support that works with any installed Tesseract languages

# Comprehensive language mapping
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
    'ha': 'Hausa', 'af': 'Afrikaans', 'zu': 'Zulu', 'xh': 'Xhosa',
    'az': 'Azerbaijani', 'be': 'Belarusian', 'bg': 'Bulgarian',
    'bs': 'Bosnian', 'ca': 'Catalan', 'ceb': 'Cebuano', 'cy': 'Welsh',
    'da': 'Danish', 'eo': 'Esperanto', 'et': 'Estonian', 'eu': 'Basque',
    'fi': 'Finnish', 'ga': 'Irish', 'gl': 'Galician', 'ht': 'Haitian Creole',
    'hy': 'Armenian', 'id': 'Indonesian', 'is': 'Icelandic', 'jw': 'Javanese',
    'ka': 'Georgian', 'kk': 'Kazakh', 'km': 'Khmer', 'ku': 'Kurdish',
    'ky': 'Kyrgyz', 'la': 'Latin', 'lb': 'Luxembourgish', 'lo': 'Lao',
    'lt': 'Lithuanian', 'lv': 'Latvian', 'mg': 'Malagasy', 'mi': 'Maori',
    'mk': 'Macedonian', 'mn': 'Mongolian', 'mr': 'Marathi', 'ms': 'Malay',
    'mt': 'Maltese', 'my': 'Burmese', 'ne': 'Nepali', 'no': 'Norwegian',
    'ny': 'Chichewa', 'ps': 'Pashto', 'sd': 'Sindhi', 'si': 'Sinhala',
    'sk': 'Slovak', 'sl': 'Slovenian', 'sm': 'Samoan', 'sn': 'Shona',
    'sq': 'Albanian', 'sr': 'Serbian', 'st': 'Sesotho', 'su': 'Sundanese',
    'tg': 'Tajik', 'tk': 'Turkmen', 'tl': 'Filipino', 'ug': 'Uyghur',
    'uz': 'Uzbek', 'yi': 'Yiddish', 'co': 'Corsican', 'haw': 'Hawaiian',
    'hmn': 'Hmong', 'ig': 'Igbo', 'jw': 'Javanese', 'lb': 'Luxembourgish',
    'mg': 'Malagasy', 'mt': 'Maltese', 'ny': 'Chichewa', 'sm': 'Samoan',
    'sn': 'Shona', 'so': 'Somali', 'st': 'Sesotho', 'su': 'Sundanese',
    'sw': 'Swahili', 'tg': 'Tajik', 'tk': 'Turkmen', 'uz': 'Uzbek',
    'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
}

# Tesseract language codes mapping
TESSERACT_LANGUAGES = {
    'af': 'afr', 'am': 'amh', 'ar': 'ara', 'as': 'asm', 'az': 'aze',
    'be': 'bel', 'bg': 'bul', 'bn': 'ben', 'bo': 'bod', 'bs': 'bos',
    'ca': 'cat', 'ceb': 'ceb', 'cs': 'ces', 'cy': 'cym', 'da': 'dan',
    'de': 'deu', 'dz': 'dzo', 'el': 'ell', 'en': 'eng', 'eo': 'epo',
    'es': 'spa', 'et': 'est', 'eu': 'eus', 'fa': 'fas', 'fi': 'fin',
    'fr': 'fra', 'ga': 'gle', 'gd': 'gla', 'gl': 'glg', 'gu': 'guj',
    'he': 'heb', 'hi': 'hin', 'hr': 'hrv', 'hu': 'hun', 'hy': 'hye',
    'id': 'ind', 'is': 'isl', 'it': 'ita', 'ja': 'jpn', 'jw': 'jav',
    'ka': 'kat', 'kk': 'kaz', 'km': 'khm', 'kn': 'kan', 'ko': 'kor',
    'ku': 'kur', 'ky': 'kir', 'la': 'lat', 'lb': 'ltz', 'lo': 'lao',
    'lt': 'lit', 'lv': 'lav', 'mg': 'mlg', 'mi': 'mri', 'mk': 'mkd',
    'ml': 'mal', 'mn': 'mon', 'mr': 'mar', 'ms': 'msa', 'mt': 'mlt',
    'my': 'mya', 'ne': 'nep', 'nl': 'nld', 'no': 'nor', 'ny': 'nya',
    'or': 'ori', 'pa': 'pan', 'pl': 'pol', 'ps': 'pus', 'pt': 'por',
    'ro': 'ron', 'ru': 'rus', 'sa': 'san', 'sd': 'snd', 'si': 'sin',
    'sk': 'slk', 'sl': 'slv', 'sm': 'smo', 'sn': 'sna', 'so': 'som',
    'sq': 'sqi', 'sr': 'srp', 'st': 'sot', 'su': 'sun', 'sv': 'swe',
    'sw': 'swa', 'ta': 'tam', 'te': 'tel', 'tg': 'tgk', 'th': 'tha',
    'tk': 'tuk', 'tl': 'tgl', 'tr': 'tur', 'tt': 'tat', 'ug': 'uig',
    'uk': 'ukr', 'ur': 'urd', 'uz': 'uzb', 'vi': 'vie', 'xh': 'xho',
    'yi': 'yid', 'yo': 'yor', 'zh': 'chi_sim', 'zu': 'zul'
}

# Script families for optimal processing
SCRIPT_FAMILIES = {
    'Latin': ['en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'sv', 'tr', 'vi', 'ro', 'nl', 'da', 'no', 'fi', 'cs', 'hu', 'sk', 'sl', 'hr', 'bs', 'sr', 'et', 'lv', 'lt', 'mt', 'ga', 'gd', 'cy', 'ca', 'gl', 'eu', 'is', 'fo', 'ms', 'id', 'sw', 'so', 'ha', 'yo', 'ig', 'af', 'zu', 'xh', 'st', 'tn', 'ts', 'ss', 've', 'nr', 'nso'],
    'Cyrillic': ['ru', 'uk', 'be', 'bg', 'sr', 'mk', 'mn', 'kk', 'ky', 'tg', 'uz', 'tt'],
    'Arabic': ['ar', 'fa', 'ur', 'ps', 'sd', 'ku', 'ug'],
    'Devanagari': ['hi', 'ne', 'mr', 'sa', 'mai', 'bh', 'awa'],
    'Bengali': ['bn', 'as'],
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
    'Malayalam': ['ml'],
    'Sinhala': ['si'],
    'Burmese': ['my'],
    'Georgian': ['ka'],
    'Armenian': ['hy'],
    'Lao': ['lo'],
    'Khmer': ['km'],
    'Tibetan': ['bo']
}

def get_script_family(lang_code):
    """Get script family for language"""
    for script, languages in SCRIPT_FAMILIES.items():
        if lang_code in languages:
            return script
    return 'Latin'  # Default fallback

def get_tesseract_code(lang_code):
    """Get Tesseract language code with intelligent fallbacks"""
    # Direct mapping first
    if lang_code in TESSERACT_LANGUAGES:
        return TESSERACT_LANGUAGES[lang_code]
    
    # Try to find similar languages
    script_family = get_script_family(lang_code)
    script_languages = SCRIPT_FAMILIES.get(script_family, ['en'])
    
    for similar_lang in script_languages:
        if similar_lang in TESSERACT_LANGUAGES:
            return TESSERACT_LANGUAGES[similar_lang]
    
    # Ultimate fallback
    return 'eng'

def get_amharic_config() -> str:
    """Get optimized Tesseract config for Amharic"""
    return '--oem 1 --psm 6 -c preserve_interword_spaces=1'

def get_ocr_config(language, script_family, image_size=None):
    """Get optimized OCR configuration for language and script"""
    base_config = "--oem 3 --dpi 300 -c tessedit_do_invert=0"
    
    # Script-specific configurations
    script_configs = {
        'Latin': "--psm 6 -c preserve_interword_spaces=1",
        'Cyrillic': "--psm 6 -c textord_min_linesize=1.5",
        'Arabic': "--psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=1 -c textord_old_baselines=1",
        'Chinese': "--psm 6 -c textord_min_linesize=2.5 -c preserve_interword_spaces=0",
        'Japanese': "--psm 6 -c textord_min_linesize=2.5 -c preserve_interword_spaces=0",
        'Korean': "--psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=0",
        'Ethiopic': "--psm 6 -c textord_min_linesize=1.8 -c preserve_interword_spaces=1",
        'Thai': "--psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=1",
        'Devanagari': "--psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=1",
        'Bengali': "--psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=1",
        'Hebrew': "--psm 6 -c textord_min_linesize=2.0 -c preserve_interword_spaces=1",
        'Greek': "--psm 6 -c textord_min_linesize=1.5 -c preserve_interword_spaces=1"
    }
    
    config = f"{base_config} {script_configs.get(script_family, '--psm 6')}"
    
    # Adjust for image characteristics
    if image_size:
        area = image_size[0] * image_size[1]
        if area > 2000000:  # Large images
            config = config.replace("--psm 6", "--psm 4")
        elif area < 100000:  # Small images
            config = config.replace("--psm 6", "--psm 8")
    
    return config

def detect_script_from_text(text):
    """Enhanced script detection from text"""
    if not text:
        return 'Latin'
    
    script_scores = {}
    
    # Define character ranges for each script
    script_ranges = {
        'Latin': lambda c: c.isascii() and c.isalpha(),
        'Cyrillic': lambda c: '\u0400' <= c <= '\u04FF',
        'Arabic': lambda c: '\u0600' <= c <= '\u06FF',
        'Devanagari': lambda c: '\u0900' <= c <= '\u097F',
        'Bengali': lambda c: '\u0980' <= c <= '\u09FF',
        'Chinese': lambda c: '\u4E00' <= c <= '\u9FFF',
        'Japanese': lambda c: ('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' or '\u4E00' <= c <= '\u9FFF'),
        'Korean': lambda c: '\uAC00' <= c <= '\uD7A3',
        'Ethiopic': lambda c: '\u1200' <= c <= '\u137F',
        'Thai': lambda c: '\u0E00' <= c <= '\u0E7F',
        'Hebrew': lambda c: '\u0590' <= c <= '\u05FF',
        'Greek': lambda c: '\u0370' <= c <= '\u03FF',
        'Tamil': lambda c: '\u0B80' <= c <= '\u0BFF',
        'Telugu': lambda c: '\u0C00' <= c <= '\u0C7F',
        'Kannada': lambda c: '\u0C80' <= c <= '\u0CFF',
        'Malayalam': lambda c: '\u0D00' <= c <= '\u0D7F',
        'Sinhala': lambda c: '\u0D80' <= c <= '\u0DFF',
        'Burmese': lambda c: '\u1000' <= c <= '\u109F',
        'Georgian': lambda c: '\u10A0' <= c <= '\u10FF',
        'Armenian': lambda c: '\u0530' <= c <= '\u058F'
    }
    
    for char in text:
        for script, check_func in script_ranges.items():
            if check_func(char):
                script_scores[script] = script_scores.get(script, 0) + 1
                break
    
    if not script_scores:
        return 'Latin'
    
    return max(script_scores.items(), key=lambda x: x[1])[0]

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
    
    # Remove whitespace for better ratio calculation
    clean_text = ''.join(text.split())
    if len(clean_text) < 2:
        return False, "Not enough content"
    
    # Count alphanumeric characters
    alpha_chars = sum(1 for c in clean_text if c.isalnum())
    alpha_ratio = alpha_chars / len(clean_text)
    
    if alpha_ratio < 0.3:  # Too many special characters
        return False, "Too many non-alphanumeric characters"
    
    return True, "Valid"

def get_fallback_strategy(primary_lang):
    """Get fallback strategy for language"""
    script_family = get_script_family(primary_lang)
    
    fallbacks = {
        'Latin': ['eng', 'spa', 'fra', 'deu', 'ita'],
        'Cyrillic': ['rus', 'ukr', 'bul'],
        'Arabic': ['ara', 'fas', 'urd'],
        'Chinese': ['chi_sim', 'chi_tra', 'eng'],
        'Japanese': ['jpn', 'eng'],
        'Korean': ['kor', 'eng'],
        'Ethiopic': ['amh', 'eng'],
        'Devanagari': ['hin', 'nep', 'eng'],
        'Bengali': ['ben', 'eng'],
        'Thai': ['tha', 'eng'],
        'Hebrew': ['heb', 'eng'],
        'Greek': ['ell', 'eng']
    }
    
    return fallbacks.get(script_family, ['eng'])

def clean_ocr_text(text, language):
    """Intelligent text cleaning based on language"""
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
    
    # Remove duplicate consecutive lines while preserving order
    unique_lines = []
    for i, line in enumerate(cleaned_lines):
        if i == 0 or line != cleaned_lines[i-1]:
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def is_garbage_line(line, language):
    """Check if line is likely garbage"""
    if len(line) < 2:
        return True
    
    # Count meaningful characters based on language script
    script_family = get_script_family(language)
    
    if script_family in ['Chinese', 'Japanese', 'Korean']:
        # For CJK, count any non-ASCII, non-punctuation as meaningful
        meaningful_chars = sum(1 for c in line if not c.isascii() and not c.isspace() and not c in '.,!?;:-()[]{}')
    else:
        # For other scripts, count alphanumeric characters
        meaningful_chars = sum(1 for c in line if c.isalnum())
    
    total_chars = len(line)
    
    if total_chars == 0:
        return True
    
    # Different thresholds for different scripts
    min_meaningful_ratio = {
        'Chinese': 0.2, 'Japanese': 0.2, 'Korean': 0.2,
        'Arabic': 0.3, 'Hebrew': 0.3,
        'Latin': 0.4, 'Cyrillic': 0.4, 'Greek': 0.4,
        'Devanagari': 0.3, 'Bengali': 0.3, 'Thai': 0.3,
        'Ethiopic': 0.3
    }
    
    threshold = min_meaningful_ratio.get(script_family, 0.4)
    return (meaningful_chars / total_chars) < threshold

def get_language_from_script(script):
    """Map script to primary language"""
    script_to_lang = {
        'Latin': 'en',
        'Cyrillic': 'ru',
        'Arabic': 'ar',
        'Chinese': 'zh',
        'Japanese': 'ja',
        'Korean': 'ko',
        'Ethiopic': 'am',
        'Devanagari': 'hi',
        'Bengali': 'bn',
        'Thai': 'th',
        'Hebrew': 'he',
        'Greek': 'el',
        'Tamil': 'ta',
        'Telugu': 'te',
        'Kannada': 'kn',
        'Malayalam': 'ml'
    }
    return script_to_lang.get(script, 'en')

def get_supported_languages():
    """Return list of supported languages"""
    return list(LANGUAGE_MAPPING.keys())

def get_language_name(code):
    """Get language name from code"""
    return LANGUAGE_MAPPING.get(code, 'Unknown')

# Language detection confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'am': 0.3,  # 30% Amharic characters
    'en': 0.6,  # 60% English characters
    'mixed': 0.1  # 10% mixed content
}

def get_language_confidence(text, language):
    """Calculate confidence level for detected language"""
    if not text:
        return 0.0
    
    total_chars = len(text.strip())
    if total_chars == 0:
        return 0.0
    
    if language == 'am':
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        return amharic_chars / total_chars
    elif language == 'en':
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        return english_chars / total_chars
    else:
        return 0.5  # Default confidence for mixed/unknown

def detect_primary_language(text):
    """Detect the primary language of text"""
    if not text or len(text.strip()) < 3:
        return 'unknown'
    
    # Count Amharic characters
    amharic_chars = sum(1 for c in text if is_amharic_character(c))
    
    # Count English letters
    english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
    
    total_chars = len(text)
    
    if total_chars == 0:
        return 'unknown'
    
    amharic_ratio = amharic_chars / total_chars
    english_ratio = english_chars / total_chars
    
    # Determine primary language
    if amharic_ratio > 0.3:
        return 'am'
    elif english_ratio > 0.7:
        return 'en'
    else:
        return 'mixed'

def validate_amharic_text(text):
    """Validate if text contains meaningful Amharic content"""
    if not text:
        return False
    
    # Count Amharic characters
    amharic_chars = sum(1 for c in text if is_amharic_character(c))
    total_chars = len(text.strip())
    
    if total_chars < 5:
        return False
    
    # At least 20% should be Amharic characters to be considered valid Amharic
    return (amharic_chars / total_chars) > 0.2

def validate_english_text(text):
    """Validate if text contains meaningful English content"""
    if not text:
        return False
    
    # Count English letters and common punctuation
    english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
    total_chars = len(text.strip())
    
    if total_chars < 5:
        return False
    
    # At least 60% should be English letters to be considered valid English
    return (english_chars / total_chars) > 0.6