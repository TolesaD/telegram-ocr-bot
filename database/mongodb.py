from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import ssl
import certifi
from datetime import datetime
import config
import urllib.parse

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_mock = False
        self.connect()
    
    def connect(self):
        """Try multiple connection strategies"""
        # Check if MongoDB URI is available
        if not config.MONGODB_URI:
            print("❌ MongoDB URI not found in environment variables")
            self.setup_mock_database()
            return
        
        connection_methods = [
            self._connect_simplified_ssl,
            self._connect_without_ssl_verification,
            self._connect_with_certifi,
        ]
        
        for method in connection_methods:
            try:
                if method():
                    print("✅ MongoDB connected successfully!")
                    self.is_mock = False
                    return
            except Exception as e:
                print(f"❌ Connection method failed: {method.__name__}: {e}")
        
        # If all methods fail, setup mock database
        print("🔴 All MongoDB connection attempts failed. Using mock database.")
        self.setup_mock_database()
    
    def _connect_simplified_ssl(self):
        """Method 1: Simplified SSL connection"""
        print("🔄 Attempting simplified SSL connection...")
        self.client = MongoClient(
            config.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        self.db = self.client[config.DATABASE_NAME]
        # Test connection
        self.client.admin.command('ping')
        return True
    
    def _connect_without_ssl_verification(self):
        """Method 2: Connection without SSL verification"""
        print("🔄 Attempting connection without SSL verification...")
        self.client = MongoClient(
            config.MONGODB_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,  # Use only this option, not tlsInsecure
            retryWrites=True,
            w='majority',
            socketTimeoutMS=20000,
            connectTimeoutMS=20000,
            serverSelectionTimeoutMS=20000
        )
        self.db = self.client[config.DATABASE_NAME]
        self.client.admin.command('ping')
        return True
    
    def _connect_with_certifi(self):
        """Method 3: Standard connection with certifi"""
        print("🔄 Attempting connection with certifi SSL...")
        self.client = MongoClient(
            config.MONGODB_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            retryWrites=True,
            w='majority',
            socketTimeoutMS=20000,
            connectTimeoutMS=20000,
            serverSelectionTimeoutMS=20000
        )
        self.db = self.client[config.DATABASE_NAME]
        self.client.admin.command('ping')
        return True

    # ... keep all the other methods the same (setup_mock_database, insert_user, etc.)

    def setup_mock_database(self):
        """Setup a complete mock database for testing"""
        print("🔄 Setting up mock database for testing...")
        self.is_mock = True
        
        # Create mock collections
        self.db = type('MockDB', (), {})()
        self.db.users = MockUsersCollection()
        self.db.requests = MockRequestsCollection()
        print("✅ Mock database setup complete!")

    def insert_user(self, user_data):
        """Insert or update user data"""
        try:
            users_collection = self.db.users
            user_data['created_at'] = user_data.get('created_at', datetime.now())
            user_data['updated_at'] = datetime.now()
            
            return users_collection.update_one(
                {'user_id': user_data['user_id']},
                {'$set': user_data},
                upsert=True
            )
        except Exception as e:
            print(f"Error in insert_user: {e}")
            return None

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            users_collection = self.db.users
            return users_collection.find_one({'user_id': user_id})
        except Exception as e:
            print(f"Error in get_user: {e}")
            return None

    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        try:
            users_collection = self.db.users
            settings['updated_at'] = datetime.now()
            return users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'settings': settings}}
            )
        except Exception as e:
            print(f"Error in update_user_settings: {e}")
            return None

    def log_ocr_request(self, request_data):
        """Log OCR request"""
        try:
            requests_collection = self.db.requests
            return requests_collection.insert_one(request_data)
        except Exception as e:
            print(f"Error in log_ocr_request: {e}")
            return None

    def get_user_stats(self, user_id):
        """Get user statistics"""
        try:
            requests_collection = self.db.requests
            if self.is_mock:
                total_requests = requests_collection.count_documents({'user_id': user_id})
                recent_requests = list(requests_collection.find({'user_id': user_id}))[-5:][::-1]
            else:
                total_requests = requests_collection.count_documents({'user_id': user_id})
                recent_requests = list(requests_collection.find({'user_id': user_id}).sort('timestamp', -1).limit(5))
            
            return {
                'total_requests': total_requests,
                'recent_requests': recent_requests
            }
        except Exception as e:
            print(f"Error in get_user_stats: {e}")
            return {'total_requests': 0, 'recent_requests': []}

# Mock Collection Classes (keep these the same)
class MockUsersCollection:
    def __init__(self):
        self.users = {}
    
    def find_one(self, query):
        user_id = query.get('user_id')
        return self.users.get(user_id)
    
    def update_one(self, query, update, upsert=False):
        try:
            user_id = query.get('user_id')
            if user_id:
                if user_id not in self.users:
                    self.users[user_id] = {}
                
                if '$set' in update:
                    self.users[user_id].update(update['$set'])
                
                return MockResult(matched_count=1, modified_count=1)
            return MockResult(matched_count=0, modified_count=0)
        except Exception as e:
            print(f"Mock update_one error: {e}")
            return MockResult(matched_count=0, modified_count=0)

class MockRequestsCollection:
    def __init__(self):
        self.requests = []
        self.request_id = 1
    
    def insert_one(self, document):
        try:
            document['_id'] = self.request_id
            self.requests.append(document)
            self.request_id += 1
            return MockResult(inserted_id=document['_id'])
        except Exception as e:
            print(f"Mock insert_one error: {e}")
            return MockResult(inserted_id=None)
    
    def count_documents(self, query):
        try:
            if not query:  # Count all documents if no query
                return len(self.requests)
            
            user_id = query.get('user_id')
            if user_id:
                return len([req for req in self.requests if req.get('user_id') == user_id])
            return 0
        except Exception as e:
            print(f"Mock count_documents error: {e}")
            return 0
    
    def find(self, query=None):
        try:
            if not query:
                return self.requests
            
            user_id = query.get('user_id')
            if user_id:
                return [req for req in self.requests if req.get('user_id') == user_id]
            return []
        except Exception as e:
            print(f"Mock find error: {e}")
            return []
    
    def sort(self, field, direction):
        """Mock sort method"""
        try:
            reverse = direction == -1
            sorted_requests = sorted(self.requests, key=lambda x: x.get(field, ''), reverse=reverse)
            return MockSortResult(sorted_requests)
        except Exception as e:
            print(f"Mock sort error: {e}")
            return MockSortResult([])

class MockResult:
    def __init__(self, matched_count=0, modified_count=0, inserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.inserted_id = inserted_id

class MockSortResult:
    def __init__(self, data):
        self.data = data
    
    def limit(self, n):
        return self.data[:n]

# Database instance
db = MongoDB()