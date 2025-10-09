from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.users = self.db.users
        self.expenses = self.db.expenses
        self.budgets = self.db.budgets

# For backward compatibility
db = Database()