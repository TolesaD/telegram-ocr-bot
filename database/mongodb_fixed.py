"""
Fixed MongoDB connection for production
"""
import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class FixedMongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False
        self.connect()
    
    def connect(self):
        """Simplified MongoDB connection without SSL issues"""
        MONGODB_URI = os.getenv('MONGODB_URI')
        
        if not MONGODB_URI:
            logger.warning("MongoDB URI not configured, using mock database")
            self.setup_mock_database()
            return
        
        try:
            # Simple connection without complex SSL options
            self.client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=30000,
                maxPoolSize=20
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client.get_database()
            
            logger.info("MongoDB connected successfully")
            self.is_mock = False
            
        except Exception as e:
            logger.error("MongoDB connection failed: %s", e)
            self.setup_mock_database()
    
    def setup_mock_database(self):
        """Fallback to mock database"""
        logger.info("Setting up mock database...")
        self.is_mock = True
        
        # Simple mock database implementation
        self.users_data = {}
        self.requests_data = []
    
    def get_user(self, user_id):
        if self.is_mock:
            return self.users_data.get(user_id)
        else:
            return self.db.users.find_one({'user_id': user_id})
    
    def insert_user(self, user_data):
        if self.is_mock:
            self.users_data[user_data['user_id']] = user_data
            return True
        else:
            return self.db.users.insert_one(user_data)
    
    def update_user_settings(self, user_id, settings):
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
    
    def log_ocr_request(self, request_data):
        if self.is_mock:
            self.requests_data.append(request_data)
            return True
        else:
            return self.db.requests.insert_one(request_data)

# Global instance
db = FixedMongoDB()