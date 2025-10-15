import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Complete language support - 80+ languages
SUPPORTED_LANGUAGES = {
    # European Languages
    'english': 'eng', 'spanish': 'spa', 'french': 'fra', 'german': 'deu',
    'italian': 'ita', 'portuguese': 'por', 'russian': 'rus', 'dutch': 'nld',
    'swedish': 'swe', 'polish': 'pol', 'ukrainian': 'ukr', 'greek': 'ell',
    'bulgarian': 'bul', 'czech': 'ces', 'danish': 'dan', 'finnish': 'fin',
    'hungarian': 'hun', 'norwegian': 'nor', 'romanian': 'ron', 'serbian': 'srp',
    'slovak': 'slk', 'slovenian': 'slv', 'catalan': 'cat', 'croatian': 'hrv',
    'estonian': 'est', 'icelandic': 'isl', 'latvian': 'lav', 'lithuanian': 'lit',
    'macedonian': 'mkd', 'maltese': 'mlt', 'albanian': 'sqi', 'basque': 'eus',
    
    # Asian Languages
    'chinese_simplified': 'chi_sim', 'chinese_traditional': 'chi_tra',
    'japanese': 'jpn', 'korean': 'kor', 'hindi': 'hin', 'bengali': 'ben',
    'tamil': 'tam', 'telugu': 'tel', 'marathi': 'mar', 'urdu': 'urd',
    'gujarati': 'guj', 'kannada': 'kan', 'malayalam': 'mal', 'odia': 'ori',
    'punjabi': 'pan', 'sanskrit': 'san', 'sinhala': 'sin', 'nepali': 'nep',
    'thai': 'tha', 'vietnamese': 'vie', 'indonesian': 'ind', 'malay': 'msa',
    'filipino': 'fil', 'burmese': 'mya', 'khmer': 'khm', 'lao': 'lao',
    'mongolian': 'mon', 'tibetan': 'bod',
    
    # Middle Eastern Languages
    'arabic': 'ara', 'hebrew': 'heb', 'persian': 'fas', 'turkish': 'tur',
    'kurdish': 'kur', 'urdu': 'urd', 'pashto': 'pus', 'sindhi': 'snd',
    'uyghur': 'uig', 'kazakh': 'kaz', 'uzbek': 'uzb', 'tajik': 'tgk',
    
    # African Languages
    'amharic': 'amh', 'afrikaans': 'afr', 'swahili': 'swa', 'yoruba': 'yor',
    'hausa': 'hau', 'igbo': 'ibo', 'zulu': 'zul', 'xhosa': 'xho',
    'somali': 'som', 'oromo': 'orm',
    
    # Other Important Languages
    'azerbaijani': 'aze', 'belarusian': 'bel', 'bosnian': 'bos',
    'galician': 'glg', 'georgian': 'kat', 'irish': 'gle', 'latin': 'lat',
    'luxembourgish': 'ltz', 'malagasy': 'mlg', 'maori': 'mri',
    'marathi': 'mar', 'nepali': 'nep', 'occitan': 'oci', 'piedmontese': 'pms',
    'tatar': 'tat', 'welsh': 'cym', 'yiddish': 'yid'
}

# Language display names
LANGUAGE_DISPLAY_NAMES = {
    # European
    'english': 'English', 'spanish': 'Spanish', 'french': 'French', 'german': 'German',
    'italian': 'Italian', 'portuguese': 'Portuguese', 'russian': 'Russian', 'dutch': 'Dutch',
    'swedish': 'Swedish', 'polish': 'Polish', 'ukrainian': 'Ukrainian', 'greek': 'Greek',
    'bulgarian': 'Bulgarian', 'czech': 'Czech', 'danish': 'Danish', 'finnish': 'Finnish',
    'hungarian': 'Hungarian', 'norwegian': 'Norwegian', 'romanian': 'Romanian', 'serbian': 'Serbian',
    'slovak': 'Slovak', 'slovenian': 'Slovenian', 'catalan': 'Catalan', 'croatian': 'Croatian',
    
    # Asian
    'chinese_simplified': 'Chinese (Simplified)', 'chinese_traditional': 'Chinese (Traditional)',
    'japanese': 'Japanese', 'korean': 'Korean', 'hindi': 'Hindi', 'bengali': 'Bengali',
    'tamil': 'Tamil', 'telugu': 'Telugu', 'marathi': 'Marathi', 'urdu': 'Urdu',
    'thai': 'Thai', 'vietnamese': 'Vietnamese', 'indonesian': 'Indonesian', 'malay': 'Malay',
    
    # Middle Eastern
    'arabic': 'Arabic', 'hebrew': 'Hebrew', 'persian': 'Persian', 'turkish': 'Turkish',
    
    # African
    'amharic': 'Amharic', 'afrikaans': 'Afrikaans', 'swahili': 'Swahili',
    
    # Add more as needed...
}

# Language groups
LANGUAGE_GROUPS = {
    'european': ['english', 'spanish', 'french', 'german', 'italian', 'portuguese', 
                'dutch', 'swedish', 'polish', 'greek', 'bulgarian', 'czech', 
                'danish', 'finnish', 'hungarian', 'norwegian', 'romanian', 
                'serbian', 'slovak', 'slovenian', 'catalan', 'croatian'],
    'asian': ['chinese_simplified', 'chinese_traditional', 'japanese', 'korean', 
             'hindi', 'bengali', 'tamil', 'telugu', 'thai', 'vietnamese', 
             'indonesian', 'malay'],
    'middle_eastern': ['arabic', 'hebrew', 'persian', 'turkish'],
    'african': ['amharic', 'afrikaans', 'swahili'],
    'indian_subcontinent': ['hindi', 'bengali', 'tamil', 'telugu', 'marathi', 'urdu'],
    'other': ['russian', 'ukrainian']
}

# Performance Settings
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB for Railway
PROCESSING_TIMEOUT = 45  # seconds

# Text Formatting Options
FORMAT_OPTIONS = ['plain', 'markdown', 'html']

# Support Email
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'tolesadebushe9@gmail.com')

# Channel Configuration
ANNOUNCEMENT_CHANNEL = "@ImageToTextConverter"
CHANNEL_USERNAME = "ImageToTextConverter"

# Admin User IDs
admin_ids_str = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = []
if admin_ids_str:
    for admin_id in admin_ids_str.split(','):
        admin_id = admin_id.strip()
        if admin_id and admin_id.isdigit():
            ADMIN_IDS.append(int(admin_id))

# Railway environment
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None