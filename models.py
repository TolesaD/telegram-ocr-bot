from datetime import datetime
from pymongo import MongoClient
from config import Config

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.users = self.db.users
        self.expenses = self.db.expenses
        self.budgets = self.db.budgets
    
    def get_user(self, user_id):
        return self.users.find_one({'user_id': user_id})
    
    def create_user(self, user_id, username, first_name):
        user_data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'created_at': datetime.now(),
            'monthly_income': 0,
            'currency': 'USD'
        }
        return self.users.insert_one(user_data)
    
    def add_expense(self, user_id, amount, category, description, date=None):
        expense_data = {
            'user_id': user_id,
            'amount': float(amount),
            'category': category,
            'description': description,
            'date': date or datetime.now(),
            'created_at': datetime.now()
        }
        return self.expenses.insert_one(expense_data)
    
    def get_user_expenses(self, user_id, month=None, year=None):
        query = {'user_id': user_id}
        if month and year:
            query['date'] = {
                '$gte': datetime(year, month, 1),
                '$lt': datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
            }
        return list(self.expenses.find(query).sort('date', -1))
    
    def set_budget(self, user_id, category, amount):
        return self.budgets.update_one(
            {'user_id': user_id, 'category': category},
            {'$set': {'amount': float(amount), 'updated_at': datetime.now()}},
            upsert=True
        )
    
    def get_user_budgets(self, user_id):
        return list(self.budgets.find({'user_id': user_id}))
    
    def get_monthly_summary(self, user_id, month, year):
        pipeline = [
            {
                '$match': {
                    'user_id': user_id,
                    'date': {
                        '$gte': datetime(year, month, 1),
                        '$lt': datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
                    }
                }
            },
            {
                '$group': {
                    '_id': '$category',
                    'total': {'$sum': '$amount'},
                    'count': {'$sum': 1}
                }
            }
        ]
        return list(self.expenses.aggregate(pipeline))