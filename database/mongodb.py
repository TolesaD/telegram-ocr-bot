# database/mongodb.py
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, mongodb_uri):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.setup()

    def setup(self):
        """Setup MongoDB connection with modern SSL handling"""
        try:
            logger.info(f"✅ MONGODB_URI found: {self.mongodb_uri[:20]}...")
            self.client = MongoClient(
                self.mongodb_uri,
                tls=True,
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=15000,
                socketTimeoutMS=30000,
                retryWrites=True,
                retryReads=True
            )
            self.db = self.client.get_database('telegram_ocr_bot')
            self.db.command('ping')  # Test connection
            logger.info("✅ MongoDB connected successfully")
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"❌ MongoDB setup failed: {e}")
            logger.info("🔄 Setting up mock database...")
            self.setup_mock()
            logger.info("✅ Mock database setup complete")
        except Exception as e:
            logger.error(f"❌ Unexpected error during MongoDB setup: {e}")
            self.setup_mock()
            logger.info("✅ Mock database setup complete")

    def setup_mock(self):
        """Setup mock database for fallback"""
        self.is_mock = True
        self.users_data = {}
        self.requests_data = []

    def get_user(self, user_id):
        """Get user data"""
        if hasattr(self, 'is_mock') and self.is_mock:
            return self.users_data.get(user_id)
        try:
            return self.db.users.find_one({'user_id': user_id})
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def insert_user(self, user_data):
        """Insert new user"""
        if hasattr(self, 'is_mock') and self.is_mock:
            self.users_data[user_data['user_id']] = user_data
            return True
        try:
            result = self.db.users.insert_one(user_data)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error inserting user: {e}")
            return False

    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        if hasattr(self, 'is_mock') and self.is_mock:
            if user_id in self.users_data:
                if 'settings' not in self.users_data[user_id]:
                    self.users_data[user_id]['settings'] = {}
                self.users_data[user_id]['settings'].update(settings)
            return True
        try:
            result = self.db.users.update_one(
                {'user_id': user_id},
                {'$set': {'settings': settings, 'updated_at': datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False

    def log_ocr_request(self, request_data):
        """Log OCR request"""
        if hasattr(self, 'is_mock') and self.is_mock:
            self.requests_data.append(request_data)
            return True
        try:
            result = self.db.ocr_requests.insert_one(request_data)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
            return False

    def get_user_stats(self, user_id):
        """Get user statistics"""
        if hasattr(self, 'is_mock') and self.is_mock:
            user_requests = [r for r in self.requests_data if r.get('user_id') == user_id]
            return {
                'total_requests': len(user_requests),
                'recent_requests': user_requests[-5:][::-1]
            }
        try:
            user_requests = list(self.db.ocr_requests.find({'user_id': user_id}))
            return {
                'total_requests': len(user_requests),
                'recent_requests': user_requests[-5:][::-1]
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total_requests': 0, 'recent_requests': []}

# Initialize database
try:
    mongodb_uri = 'mongodb+srv://telegram-bot-user:KJMPN6R7SctEtlZZ@pythoncluster.dufidzj.mongodb.net/telegram_ocr_bot?retryWrites=true&w=majority'
    db = Database(mongodb_uri)
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    db = Database(None)