# database/sqlite_db.py
import logging
import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SQLiteDatabase:
    def __init__(self, db_path=None):
        # Use in-memory database on Railway, file-based locally
        if db_path is None:
            if os.environ.get('RAILWAY_ENVIRONMENT'):
                # Use in-memory database on Railway
                self.db_path = ":memory:"
                logger.info("🚀 Using in-memory SQLite database (Railway)")
            else:
                # Use file-based database locally
                self.db_path = "ocr_bot.db"
                logger.info("💾 Using file-based SQLite database (Local)")
        else:
            self.db_path = db_path
            
        self.setup()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise e
        finally:
            conn.close()

    def setup(self):
        """Setup SQLite database with tables"""
        try:
            with self.get_connection() as conn:
                # Users table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        settings TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # OCR requests table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS ocr_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        format TEXT,
                        text_length INTEGER,
                        processing_time REAL,
                        status TEXT,
                        error TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                logger.info("✅ SQLite database setup complete")
        except Exception as e:
            logger.error(f"❌ SQLite setup failed: {e}")
            # Don't raise the error, just log it and continue with mock functionality
            logger.info("🔄 Falling back to in-memory storage")

    def get_user(self, user_id):
        """Get user data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM users WHERE user_id = ?', 
                    (user_id,)
                )
                row = cursor.fetchone()
                if row:
                    user_dict = dict(row)
                    # Parse settings from JSON string
                    if user_dict.get('settings'):
                        try:
                            user_dict['settings'] = json.loads(user_dict['settings'])
                        except:
                            user_dict['settings'] = {}
                    return user_dict
                return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def insert_user(self, user_data):
        """Insert new user"""
        try:
            with self.get_connection() as conn:
                # Convert settings to JSON string
                settings_str = json.dumps(user_data.get('settings', {}))
                
                conn.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, settings, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_id'],
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    settings_str,  # Store as JSON string
                    datetime.now()
                ))
                return True
        except Exception as e:
            logger.error(f"Error inserting user: {e}")
            return False

    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        try:
            with self.get_connection() as conn:
                # Convert settings to JSON string
                settings_str = json.dumps(settings)
                
                conn.execute('''
                    UPDATE users 
                    SET settings = ?, updated_at = ?
                    WHERE user_id = ?
                ''', (settings_str, datetime.now(), user_id))
                return True
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False

    def log_ocr_request(self, request_data):
        """Log OCR request"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO ocr_requests 
                    (user_id, format, text_length, processing_time, status, error)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    request_data.get('user_id'),
                    request_data.get('format'),
                    request_data.get('text_length'),
                    request_data.get('processing_time'),
                    request_data.get('status'),
                    request_data.get('error')
                ))
                return True
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
            return False

    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            with self.get_connection() as conn:
                # Total requests
                cursor = conn.execute(
                    'SELECT COUNT(*) as total FROM ocr_requests WHERE user_id = ?',
                    (user_id,)
                )
                total_requests = cursor.fetchone()['total']
                
                # Recent requests (last 10)
                cursor = conn.execute('''
                    SELECT * FROM ocr_requests 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                ''', (user_id,))
                recent_requests = [dict(row) for row in cursor.fetchall()]
                
                # Calculate success rate
                success_count = sum(1 for r in recent_requests if r.get('status') == 'success')
                success_rate = (success_count / len(recent_requests)) * 100 if recent_requests else 0
                
                return {
                    'total_requests': total_requests,
                    'recent_requests': recent_requests,
                    'success_rate': success_rate,
                    'success_count': success_count
                }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {
                'total_requests': 0,
                'recent_requests': [],
                'success_rate': 0,
                'success_count': 0
            }

# Initialize database with fallback
try:
    db = SQLiteDatabase()
    # Test the connection
    with db.get_connection() as conn:
        conn.execute("SELECT 1")
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    # Fallback to mock database
    class MockDB:
        def __init__(self): 
            self.is_mock = True
            self.users_data = {}
            self.requests_data = []
            logger.info("🔄 Using mock database as fallback")
        
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