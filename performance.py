# config/performance.py
import os

# Performance settings
class PerformanceConfig:
    # Image processing settings
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    PROCESSING_TIMEOUT = 45  # seconds
    MAX_CONCURRENT_REQUESTS = 3
    
    # OCR settings
    OCR_TIMEOUT = 30
    FAST_OCR_TIMEOUT = 15
    
    # Caching settings
    ENABLE_CACHING = True
    CACHE_DURATION = 300  # 5 minutes
    
    # Memory management
    MAX_WORKERS = 4
    CLEANUP_INTERVAL = 60  # seconds
    
    @classmethod
    def get_optimized_ocr_config(cls, language):
        """Get optimized OCR configuration for specific language"""
        configs = {
            'amh': '--oem 1 --psm 6 -c preserve_interword_spaces=1',
            'eng': '--oem 3 --psm 6',
            'default': '--oem 3 --psm 6'
        }
        return configs.get(language, configs['default'])

# Environment-based configuration
def get_performance_settings():
    """Get performance settings based on environment"""
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    if is_railway:
        # Railway-optimized settings
        return {
            'MAX_WORKERS': 3,
            'MAX_CONCURRENT_REQUESTS': 2,
            'OCR_TIMEOUT': 25
        }
    else:
        # Local development settings
        return {
            'MAX_WORKERS': 4,
            'MAX_CONCURRENT_REQUESTS': 3,
            'OCR_TIMEOUT': 30
        }