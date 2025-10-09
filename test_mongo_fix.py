import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

# Test different connection options
uri = os.getenv('MONGODB_URI')

print("Testing MongoDB connection...")

try:
    # Option 1: Basic connection
    client = pymongo.MongoClient(uri)
    client.admin.command('ping')
    print("✅ Connection successful with basic settings")
except Exception as e:
    print(f"❌ Basic failed: {e}")

try:
    # Option 2: With SSL bypass
    client = pymongo.MongoClient(uri, tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("✅ Connection successful with SSL bypass")
except Exception as e:
    print(f"❌ SSL bypass failed: {e}")

try:
    # Option 3: Without SSL
    uri_no_ssl = uri.replace('mongodb+srv://', 'mongodb://').replace('?retryWrites', '?ssl=false&retryWrites')
    client = pymongo.MongoClient(uri_no_ssl)
    client.admin.command('ping')
    print("✅ Connection successful without SSL")
except Exception as e:
    print(f"❌ Without SSL failed: {e}")