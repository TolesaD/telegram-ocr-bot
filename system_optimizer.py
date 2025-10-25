# system_optimizer.py
import os
import psutil

def optimize_system_for_ocr():
    """Optimize system settings for better OCR performance"""
    # Set Tesseract cache size
    os.environ['OMP_THREAD_LIMIT'] = '1'
    
    # Limit memory usage
    process = psutil.Process()
    if hasattr(process, 'rlimit'):
        try:
            import resource
            # Limit memory to 1GB
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
        except:
            pass

# Call this at startup
optimize_system_for_ocr()