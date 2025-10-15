import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enhanced language support
SUPPORTED_LANGUAGES = {
    'english': 'eng', 'spanish': 'spa', 'french': 'fra', 'german': 'deu',
    'italian': 'ita', 'portuguese': 'por', 'russian': 'rus', 
    'chinese_simplified': 'chi_sim', 'japanese': 'jpn', 'korean': 'kor',
    'arabic': 'ara', 'hindi': 'hin', 'turkish': 'tur', 'dutch': 'nld',
    'swedish': 'swe', 'polish': 'pol', 'ukrainian': 'ukr', 'greek': 'ell',
    # Add more languages from the 80+ supported
    'afrikaans': 'afr', 'albanian': 'sqi', 'amharic': 'amh', 'arabic': 'ara',
    'armenian': 'hye', 'azerbaijani': 'aze', 'basque': 'eus', 'belarusian': 'bel',
    'bengali': 'ben', 'bosnian': 'bos', 'bulgarian': 'bul', 'burmese': 'mya',
    'catalan': 'cat', 'cebuano': 'ceb', 'chinese': 'chi_sim', 'croatian': 'hrv',
    'czech': 'ces', 'danish': 'dan', 'dutch': 'nld', 'esperanto': 'epo',
    'estonian': 'est', 'filipino': 'tgl', 'finnish': 'fin', 'french': 'fra',
    'galician': 'glg', 'georgian': 'kat', 'german': 'deu', 'greek': 'ell',
    'gujarati': 'guj', 'haitian': 'hat', 'hausa': 'hau', 'hebrew': 'heb',
    'hindi': 'hin', 'hmong': 'hmn', 'hungarian': 'hun', 'icelandic': 'isl',
    'igbo': 'ibo', 'indonesian': 'ind', 'irish': 'gle', 'italian': 'ita',
    'japanese': 'jpn', 'javanese': 'jav', 'kannada': 'kan', 'kazakh': 'kaz',
    'khmer': 'khm', 'korean': 'kor', 'kurdish': 'kur', 'kyrgyz': 'kir',
    'lao': 'lao', 'latin': 'lat', 'latvian': 'lav', 'lithuanian': 'lit',
    'luxembourgish': 'ltz', 'macedonian': 'mkd', 'malagasy': 'mlg',
    'malay': 'msa', 'malayalam': 'mal', 'maltese': 'mlt', 'maori': 'mri',
    'marathi': 'mar', 'mongolian': 'mon', 'nepali': 'nep', 'norwegian': 'nor',
    'nyanja': 'nya', 'pashto': 'pus', 'persian': 'fas', 'polish': 'pol',
    'portuguese': 'por', 'punjabi': 'pan', 'romanian': 'ron', 'russian': 'rus',
    'samoan': 'smo', 'scots': 'sco', 'serbian': 'srp', 'sesotho': 'sot',
    'shona': 'sna', 'sindhi': 'snd', 'sinhala': 'sin', 'slovak': 'slk',
    'slovenian': 'slv', 'somali': 'som', 'southern': 'sot', 'sundanese': 'sun',
    'swahili': 'swa', 'swedish': 'swe', 'tajik': 'tgk', 'tamil': 'tam',
    'telugu': 'tel', 'thai': 'tha', 'turkish': 'tur', 'ukrainian': 'ukr',
    'urdu': 'urd', 'uzbek': 'uzb', 'vietnamese': 'vie', 'welsh': 'cym',
    'xhosa': 'xho', 'yiddish': 'yid', 'yoruba': 'yor', 'zulu': 'zul'
}

# Performance Settings
MAX_IMAGE_SIZE = 15 * 1024 * 1024  # 15MB
PROCESSING_TIMEOUT = 30  # seconds

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