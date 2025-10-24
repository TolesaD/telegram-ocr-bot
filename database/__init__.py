# database/__init__.py
import logging
import os

logger = logging.getLogger(__name__)

# Try PostgreSQL first, fallback to SQLite
try:
    from .postgres_db import PostgresDatabase
    if os.environ.get('DATABASE_URL'):
        db = PostgresDatabase()
        logger.info("✅ Using PostgreSQL database")
    else:
        raise ImportError("No DATABASE_URL found")
except Exception as e:
    logger.warning(f"PostgreSQL not available: {e}")
    try:
        from .sqlite_db import SQLiteDatabase
        db = SQLiteDatabase()
        logger.info("✅ Using SQLite database as fallback")
    except Exception as e2:
        logger.error(f"Both databases failed: {e2}")
        # Fallback to mock database
        class MockDB:
            def __init__(self): 
                self.is_mock = True
                self.users_data = {}
                self.requests_data = []
                logger.info("🔄 Using mock database as final fallback")
            
            def get_user(self, user_id): 
                return self.users_data.get(user_id)
            
            def insert_user(self, user_data): 
                self.users_data[user_data['user_id']] = user_data
                return True
            
            def update_user_settings(self, user_id, settings): 
                if user_id in self.users_data:
                    if 'settings' not in self.users_data[user_id]:
                        self.users_data[user_id]['settings'] = {}
                    self.users_data[user_id]['settings'].update(settings)
                return True
            
            def log_ocr_request(self, request_data): 
                self.requests_data.append(request_data)
                return True
            
            def get_user_stats(self, user_id): 
                user_requests = [r for r in self.requests_data if r.get('user_id') == user_id]
                return {
                    'total_requests': len(user_requests),
                    'recent_requests': user_requests[-10:][::-1],
                    'success_rate': 100,
                    'success_count': len(user_requests)
                }
        
        db = MockDB()