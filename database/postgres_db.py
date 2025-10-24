# database/postgres_db.py
import logging
import os
import json
from datetime import datetime
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class PostgresDatabase:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        self.setup()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(self.database_url)
        conn.autocommit = False
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise e
        finally:
            conn.close()

    def setup(self):
        """Setup PostgreSQL database with tables"""
        try:
            with self.get_connection() as cursor:
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        settings JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # OCR requests table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ocr_requests (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        format TEXT,
                        text_length INTEGER,
                        processing_time REAL,
                        status TEXT,
                        error TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                logger.info("✅ PostgreSQL database setup complete")
        except Exception as e:
            logger.error(f"❌ PostgreSQL setup failed: {e}")
            raise

    def get_user(self, user_id):
        """Get user data"""
        try:
            with self.get_connection() as cursor:
                cursor.execute(
                    'SELECT * FROM users WHERE user_id = %s', 
                    (user_id,)
                )
                row = cursor.fetchone()
                if row:
                    user_dict = dict(row)
                    # Settings are already JSON in PostgreSQL
                    if user_dict.get('settings') is None:
                        user_dict['settings'] = {}
                    return user_dict
                return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def insert_user(self, user_data):
        """Insert new user"""
        try:
            with self.get_connection() as cursor:
                cursor.execute('''
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, settings, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    settings = EXCLUDED.settings,
                    updated_at = EXCLUDED.updated_at
                ''', (
                    user_data['user_id'],
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    json.dumps(user_data.get('settings', {})),
                    datetime.now()
                ))
                return True
        except Exception as e:
            logger.error(f"Error inserting user: {e}")
            return False

    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        try:
            with self.get_connection() as cursor:
                cursor.execute('''
                    UPDATE users 
                    SET settings = %s, updated_at = %s
                    WHERE user_id = %s
                ''', (json.dumps(settings), datetime.now(), user_id))
                return True
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False

    def log_ocr_request(self, request_data):
        """Log OCR request"""
        try:
            with self.get_connection() as cursor:
                cursor.execute('''
                    INSERT INTO ocr_requests 
                    (user_id, format, text_length, processing_time, status, error)
                    VALUES (%s, %s, %s, %s, %s, %s)
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
            with self.get_connection() as cursor:
                # Total requests
                cursor.execute(
                    'SELECT COUNT(*) as total FROM ocr_requests WHERE user_id = %s',
                    (user_id,)
                )
                total_requests = cursor.fetchone()['total']
                
                # Recent requests (last 10)
                cursor.execute('''
                    SELECT * FROM ocr_requests 
                    WHERE user_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                ''', (user_id,))
                recent_requests = [dict(row) for row in cursor.fetchall()]
                
                # Calculate success rate
                cursor.execute('''
                    SELECT COUNT(*) as success_count FROM ocr_requests 
                    WHERE user_id = %s AND status = 'success'
                ''', (user_id,))
                success_count = cursor.fetchone()['success_count']
                
                success_rate = (success_count / total_requests) * 100 if total_requests > 0 else 0
                
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