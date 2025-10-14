from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import logging
import os
import config

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False
        self.connect()
    
    def connect(self):
        """Connect to MongoDB with production settings"""
        if not config.MONGODB_URI:
            logger.warning("MongoDB URI not configured, using mock database")
            self.setup_mock_database()
            return
        
        try:
            # Simple connection for Railway
            self.client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=30000,
                maxPoolSize=20,
                retryWrites=True,
                retryReads=True
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            
            logger.info("✅ MongoDB connected successfully")
            self.is_mock = False
            
            # Create indexes for better performance
            self._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.setup_mock_database()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index for user queries
            self.db.users.create_index("user_id", unique=True)
            self.db.users.create_index("created_at")
            
            # Index for OCR request queries
            self.db.requests.create_index("user_id")
            self.db.requests.create_index("timestamp")
            self.db.requests.create_index([("user_id", 1), ("timestamp", -1)])
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
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
                return self.db.users.update_one(
                    {'user_id': user_id},
                    {'$set': {'settings': settings}}
                )
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return None
    
    def update_user_channel_status(self, user_id, status_data):
        """Update user's channel status"""
        try:
            if self.is_mock:
                if user_id in self.users_data:
                    self.users_data[user_id].update(status_data)
                return True
            else:
                return self.db.users.update_one(
                    {'user_id': user_id},
                    {'$set': status_data}
                )
        except Exception as e:
            logger.error(f"Error updating channel status: {e}")
            return None
    
    def log_ocr_request(self, request_data):
        """Log OCR request"""
        try:
            if self.is_mock:
                self.requests_data.append(request_data)
                return True
            else:
                return self.db.requests.insert_one(request_data)
        except Exception as e:
            logger.error(f"Error logging OCR request: {e}")
            return None
    
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

    def setup_mock_database(self):
        """Setup mock database for production fallback"""
        logger.info("🔄 Setting up production mock database...")
        self.is_mock = True
        self.users_data = {}
        self.requests_data = []
        logger.info("✅ Production mock database setup complete")

# Database instance
db = MongoDB()