# ocr_engine/language_support.py
# Enhanced language support with 100+ languages and improved Amharic handling

LANGUAGE_MAPPING = {
    'af': 'Afrikaans', 'ar': 'Arabic', 'az': 'Azerbaijani', 'be': 'Belarusian',
    'bg': 'Bulgarian', 'bn': 'Bengali', 'bs': 'Bosnian', 'ca': 'Catalan',
    'ceb': 'Cebuano', 'cs': 'Czech', 'cy': 'Welsh', 'da': 'Danish',
    'de': 'German', 'el': 'Greek', 'en': 'English', 'eo': 'Esperanto',
    'es': 'Spanish', 'et': 'Estonian', 'eu': 'Basque', 'fa': 'Persian',
    'fi': 'Finnish', 'fr': 'French', 'ga': 'Irish', 'gl': 'Galician',
    'gu': 'Gujarati', 'ha': 'Hausa', 'hi': 'Hindi', 'hr': 'Croatian',
    'ht': 'Haitian', 'hu': 'Hungarian', 'hy': 'Armenian', 'id': 'Indonesian',
    'ig': 'Igbo', 'is': 'Icelandic', 'it': 'Italian', 'iw': 'Hebrew',
    'ja': 'Japanese', 'jw': 'Javanese', 'ka': 'Georgian', 'kk': 'Kazakh',
    'km': 'Khmer', 'kn': 'Kannada', 'ko': 'Korean', 'la': 'Latin',
    'lo': 'Lao', 'lt': 'Lithuanian', 'lv': 'Latvian', 'mg': 'Malagasy',
    'mi': 'Maori', 'mk': 'Macedonian', 'ml': 'Malayalam', 'mn': 'Mongolian',
    'mr': 'Marathi', 'ms': 'Malay', 'mt': 'Maltese', 'my': 'Myanmar',
    'ne': 'Nepali', 'nl': 'Dutch', 'no': 'Norwegian', 'ny': 'Chichewa',
    'pa': 'Punjabi', 'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian',
    'ru': 'Russian', 'si': 'Sinhala', 'sk': 'Slovak', 'sl': 'Slovenian',
    'so': 'Somali', 'sq': 'Albanian', 'sr': 'Serbian', 'st': 'Sesotho',
    'su': 'Sundanese', 'sv': 'Swedish', 'sw': 'Swahili', 'ta': 'Tamil',
    'te': 'Telugu', 'tg': 'Tajik', 'th': 'Thai', 'tl': 'Filipino',
    'tr': 'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'uz': 'Uzbek',
    'vi': 'Vietnamese', 'xh': 'Xhosa', 'yi': 'Yiddish', 'yo': 'Yoruba',
    'zh': 'Chinese', 'zu': 'Zulu',
    # Added more for African and Indian
    'am': 'Amharic', 'bm': 'Bambara', 'ff': 'Fula', 'lg': 'Luganda',
    'ln': 'Lingala', 'lu': 'Luba-Katanga', 'nd': 'North Ndebele',
    'om': 'Oromo', 'rn': 'Kirundi', 'rw': 'Kinyarwanda', 'sg': 'Sango',
    'sn': 'Shona', 'ss': 'Swati', 'ti': 'Tigrinya', 'tn': 'Tswana',
    'ts': 'Tsonga', 've': 'Venda', 'wo': 'Wolof',
    'as': 'Assamese', 'bh': 'Bihari', 'or': 'Oriya', 'sd': 'Sindhi'
}

# Tesseract language codes (expanded for all)
TESSERACT_LANGUAGES = {
    'af': 'afr', 'ar': 'ara', 'az': 'aze', 'be': 'bel', 'bg': 'bul',
    'bn': 'ben', 'bs': 'bos', 'ca': 'cat', 'ceb': 'ceb', 'cs': 'ces',
    'cy': 'cym', 'da': 'dan', 'de': 'deu', 'el': 'ell', 'en': 'eng',
    'eo': 'epo', 'es': 'spa', 'et': 'est', 'eu': 'eus', 'fa': 'fas',
    'fi': 'fin', 'fr': 'fra', 'ga': 'gle', 'gl': 'glg', 'gu': 'guj',
    'he': 'heb', 'hi': 'hin', 'hr': 'hrv', 'hu': 'hun', 'hy': 'hye',
    'id': 'ind', 'is': 'isl', 'it': 'ita', 'ja': 'jpn', 'jw': 'jav',
    'ka': 'kat', 'kk': 'kaz', 'km': 'khm', 'kn': 'kan', 'ko': 'kor',
    'la': 'lat', 'lo': 'lao', 'lt': 'lit', 'lv': 'lav', 'mg': 'mlg',
    'mi': 'mri', 'mk': 'mkd', 'ml': 'mal', 'mn': 'mon', 'mr': 'mar',
    'ms': 'msa', 'mt': 'mlt', 'my': 'mya', 'ne': 'nep', 'nl': 'nld',
    'no': 'nor', 'ny': 'nya', 'pa': 'pan', 'pl': 'pol', 'pt': 'por',
    'ro': 'ron', 'ru': 'rus', 'si': 'sin', 'sk': 'slk', 'sl': 'slv',
    'so': 'som', 'sq': 'sqi', 'sr': 'srp', 'st': 'sot', 'su': 'sun',
    'sv': 'swe', 'sw': 'swa', 'ta': 'tam', 'te': 'tel', 'tg': 'tgk',
    'th': 'tha', 'tl': 'tgl', 'tr': 'tur', 'uk': 'ukr', 'ur': 'urd',
    'uz': 'uzb', 'vi': 'vie', 'xh': 'xho', 'yi': 'yid', 'yo': 'yor',
    'zh': 'chi_sim', 'zu': 'zul',
    # Enhanced support for African languages
    'am': 'amh+amh_vert', 'as': 'asm', 'bm': 'bam', 'ff': 'ful', 'lg': 'lug',
    'ln': 'lin', 'lu': 'lua', 'nd': 'nde', 'om': 'orm', 'rn': 'run',
    'rw': 'kin', 'sg': 'sag', 'sn': 'sna', 'ss': 'ssw', 'ti': 'tir',
    'tn': 'tsn', 'ts': 'tso', 've': 'ven', 'wo': 'wol', 'or': 'ori',
    'sd': 'snd'
}

# Language families for better script detection
LANGUAGE_FAMILIES = {
    'am': 'Ethiopic',
    'ar': 'Arabic',
    'he': 'Hebrew',
    'ru': 'Cyrillic',
    'el': 'Greek',
    'th': 'Thai',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'hi': 'Devanagari',
    'ta': 'Tamil',
    'te': 'Telugu',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'en': 'Latin'
}

# Amharic-specific configuration
AMHARIC_CONFIG = {
    'psm': '6',  # Uniform block of text
    'oem': '1',  # Neural nets LSTM engine only
    'config': '-c tessedit_char_whitelist=፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼።፣፤፥፦፧፨፠፡።፣፤፥፦፧፨ᎀᎁᎂᎃᎄᎅᎆᎇᎈᎉᎊᎋᎌᎍᎎᎏ᎐᎑᎒᎓᎔᎕᎖᎗᎘᎙᎚᎛᎜᎝᎞᎟ᎠᎡᎢᎣᎤᎥᎦᎧᎨᎩᎪᎫᎬᎭᎮᎯᎰᎱᎲᎳᎴᎵᎶᎷᎸᎹᎺᎻᎼᎽᎾᎿᏀᏁᏂᏃᏄᏅᏆᏇᏈᏉᏊᏋᏌᏍᏎᏏᏐᏑᏒᏓᏔᏕᏖᏗᏘᏙᏚᏛᏜᏝᏞᏟᏠᏡᏢᏣᏤᏥᏦᏧᏨᏩᏪᏫᏬᏭᏮᏯᏰᏱᏲᏳᏴᏵabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:-()[]{}'
}

def get_supported_languages():
    """Return list of supported languages"""
    return list(LANGUAGE_MAPPING.keys())

def get_language_name(code):
    """Get language name from code"""
    return LANGUAGE_MAPPING.get(code, 'Unknown')

def get_tesseract_code(lang_code):
    """Get Tesseract language code with enhanced Amharic support"""
    if lang_code == 'am':
        # Try multiple Amharic configurations
        return 'amh+amh_vert+eng'  # Fallback to English if Amharic fails
    return TESSERACT_LANGUAGES.get(lang_code, 'eng')

def get_language_family(lang_code):
    """Get language family for script-specific processing"""
    return LANGUAGE_FAMILIES.get(lang_code, 'Latin')

def is_complex_script(lang_code):
    """Check if language uses complex script requiring special processing"""
    complex_scripts = ['am', 'ar', 'he', 'th', 'zh', 'ja', 'ko', 'hi']
    return lang_code in complex_scripts

def get_amharic_config():
    """Get Amharic-specific Tesseract configuration"""
    return f'--oem {AMHARIC_CONFIG["oem"]} --psm {AMHARIC_CONFIG["psm"]} {AMHARIC_CONFIG["config"]}'

def is_amharic_character(char):
    """Check if character is in Amharic Unicode range"""
    return ('\u1200' <= char <= '\u137F' or 
            '\u2D80' <= char <= '\u2DDF' or 
            '\uAB00' <= char <= '\uAB2F')

def get_lang_from_script(script):
    """Map script to language code with enhanced detection"""
    mapping = {
        'Latin': 'eng',
        'Cyrillic': 'rus',
        'Arabic': 'ara',
        'Devanagari': 'hin',
        'HanS': 'chi_sim',
        'Hangul': 'kor',
        'Japanese': 'jpn',
        'Tamil': 'tam',
        'Telugu': 'tel',
        'Kannada': 'kan',
        'Malayalam': 'mal',
        'Gujarati': 'guj',
        'Gurmukhi': 'pan',
        'Bengali': 'ben',
        'Amharic': 'amh',
        'Ethiopic': 'amh',
        'Ge\'ez': 'amh',  # Add Ge'ez as another name for Ethiopic script
        'Hebrew': 'heb',
        'Armenian': 'hye',
        'Georgian': 'kat',
        'Thai': 'tha',
        'Lao': 'lao',
        'Khmer': 'khm',
        'Myanmar': 'mya',
        'Sinhala': 'sin',
        'Greek': 'ell',
        'Oriya': 'ori',
        'Sindhi': 'snd',
        'Tibetan': 'bod'
    }
    return mapping.get(script, 'eng')  # Default to English for unknown scripts

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
        return 'amh'
    elif english_ratio > 0.7:
        return 'eng'
    else:
        return 'mixed'

def get_optimal_ocr_config(language):
    """Get optimal OCR configuration for specific language"""
    configs = {
        'amh': '--oem 1 --psm 6 -c preserve_interword_spaces=1',
        'eng': '--oem 3 --psm 6 -c preserve_interword_spaces=1',
        'mixed': '--oem 3 --psm 3 -c preserve_interword_spaces=1',
        'unknown': '--oem 3 --psm 6 -c preserve_interword_spaces=1'
    }
    return configs.get(language, configs['unknown'])

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

# Language detection confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'amh': 0.3,  # 30% Amharic characters
    'eng': 0.6,  # 60% English characters
    'mixed': 0.1  # 10% mixed content
}

def get_language_confidence(text, language):
    """Calculate confidence level for detected language"""
    if not text:
        return 0.0
    
    total_chars = len(text.strip())
    if total_chars == 0:
        return 0.0
    
    if language == 'amh':
        amharic_chars = sum(1 for c in text if is_amharic_character(c))
        return amharic_chars / total_chars
    elif language == 'eng':
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        return english_chars / total_chars
    else:
        return 0.5  # Default confidence for mixed/unknown