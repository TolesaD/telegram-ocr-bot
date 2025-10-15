import logging
import sys

class ProductionFormatter(logging.Formatter):
    """Production formatter with emoji support"""
    def format(self, record):
        original = super().format(record)
        if record.levelname == 'INFO':
            return f"📊 {original}"
        elif record.levelname == 'WARNING':
            return f"⚠️ {original}"
        elif record.levelname == 'ERROR':
            return f"❌ {original}"
        elif record.levelname == 'DEBUG':
            return f"🔍 {original}"
        return original

def setup_logger():
    """Setup production logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Apply production formatter
    for handler in logging.getLogger().handlers:
        handler.setFormatter(ProductionFormatter())
    
    return logging.getLogger(__name__)