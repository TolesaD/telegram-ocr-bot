# Enhanced language support with 80+ languages
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
    'zh': 'Chinese', 'zu': 'Zulu'
}

# Tesseract language codes
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
    'zh': 'chi_sim', 'zu': 'zul'
}

def get_supported_languages():
    """Return list of supported languages"""
    return list(LANGUAGE_MAPPING.keys())

def get_language_name(code):
    """Get language name from code"""
    return LANGUAGE_MAPPING.get(code, 'Unknown')

def get_tesseract_code(lang_code):
    """Get Tesseract language code"""
    return TESSERACT_LANGUAGES.get(lang_code, 'eng')