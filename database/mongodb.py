from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False
        self.connect()
    
    def connect(self):
        """Connect to MongoDB with SSL handling"""
        mongodb_uri = os.getenv('MONGODB_URI')
        
        if not mongodb_uri:
            logger.warning("MongoDB URI not configured, using mock database")
            self.setup_mock_database()
            return
        
        try:
            # Try connection with TLS
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=30000,
                tls=True,
                tlsAllowInvalidCertificates=True
            )
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            logger.info("✅ MongoDB connected successfully (with TLS)")
            self.is_mock = False
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            logger.info("🔄 Falling back to mock database")
            self.setup_mock_database()
    
    def setup_mock_database(self):
        """Setup mock database"""
        logger.info("🔄 Setting up mock database...")
        self.is_mock = True
        self.users_data = {}
        self.requests_data = []
        logger.info("✅ Mock database setup complete")
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            if self.is_mock:
                return self.users_data.get(user_id)
            return self.db.users.find_one({'user_id': user_id})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def insert_user(self, user_data):
        """Insert or update user data"""
        try:
            if self.is_mock:
                self.users_data[user_data['user_id']] = user_data
                return True
            else:
                result = self.db.users.update_one(
                    {'user_id': user_data['user_id']},
                    {'$set': user_data},
                    upsert=True
                )
                return result.upserted_id is not None
        except Exception as e:
            logger.error(f"Error inserting user: {e}")
            return False
    
    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        try:
            settings['updated_at'] = datetime.now()
            if self.is_mock:
                if user_id in self.users_data:
                    if 'settings' not in self.users_data[user_id]:
                        self.users_data[user_id]['settings'] = {}
                    self.users_data[user_id]['settings'].update(settings)
                return True
            else:
                result = self.db.users.update_one(
                    {'user_id': user_id},
                    {'$set': {'settings': settings}}
                )
                return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False
    
    def log_ocr_request(self, request_data):
        """Log OCR request"""
        try:
            if self.is_mock:
                self.requests_data.append(request_data)
                return True
            else:
                result = self.db.requests.insert_one(request_data)
                return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
            return False
    
    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            if self.is_mock:
                total_requests = len([r for r in self.requests_data if r.get('user_id') == user_id])
                recent_requests = [r for r in self.requests_data if r.get('user_id') == user_id][-5:][::-1]
            else:
                total_requests = self.db.requests.count_documents({'user_id': user_id})
                recent_requests = list(self.db.requests.find({'user_id': user_id}).sort('timestamp', -1).limit(5))
            
            return {
                'total_requests': total_requests,
                'recent_requests': recent_requests
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total_requests': 0, 'recent_requests': []}

# ⚠️ CRITICAL: This line must be at the end to create the db instance
db = MongoDB()