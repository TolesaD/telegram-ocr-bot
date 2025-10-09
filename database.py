from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta
import logging
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.DATABASE_NAME]
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise
    
    def get_collection(self, name):
        return self.db[name]
    
    def close(self):
        if self.client:
            self.client.close()

class ReminderManager:
    def __init__(self):
        self.db = Database()
        self.reminders = self.db.get_collection('reminders')
    
    def create_reminder(self, user_id, chat_id, time, message, recurrence=None):
        reminder = {
            'user_id': user_id,
            'chat_id': chat_id,
            'time': time,
            'message': message,
            'recurrence': recurrence,
            'next_reminder': self._calculate_next_reminder(time, recurrence),
            'active': True,
            'created_at': datetime.utcnow()
        }
        result = self.reminders.insert_one(reminder)
        return str(result.inserted_id)
    
    def get_user_reminders(self, user_id):
        return list(self.reminders.find({
            'user_id': user_id,
            'active': True
        }).sort('next_reminder', 1))
    
    def get_due_reminders(self):
        return list(self.reminders.find({
            'next_reminder': {'$lte': datetime.utcnow()},
            'active': True
        }))
    
    def cancel_reminder(self, reminder_id, user_id):
        from bson.objectid import ObjectId
        result = self.reminders.update_one(
            {'_id': ObjectId(reminder_id), 'user_id': user_id},
            {'$set': {'active': False}}
        )
        return result.modified_count > 0
    
    def update_next_reminder(self, reminder_id):
        from bson.objectid import ObjectId
        reminder = self.reminders.find_one({'_id': ObjectId(reminder_id)})
        if reminder:
            next_reminder = self._calculate_next_reminder(
                reminder['time'], 
                reminder['recurrence']
            )
            self.reminders.update_one(
                {'_id': ObjectId(reminder_id)},
                {'$set': {'next_reminder': next_reminder}}
            )
    
    def _calculate_next_reminder(self, time_str, recurrence):
        now = datetime.utcnow()
        reminder_time = datetime.strptime(time_str, '%H:%M').time()
        
        if recurrence == 'daily':
            next_reminder = datetime.combine(now.date(), reminder_time)
            if next_reminder <= now:
                next_reminder += timedelta(days=1)
        
        elif recurrence == 'weekly':
            next_reminder = datetime.combine(now.date(), reminder_time)
            days_ahead = 6 - now.weekday()  # Next week
            if days_ahead <= 0:
                days_ahead += 7
            next_reminder += timedelta(days=days_ahead)
        
        elif recurrence == 'monthly':
            next_reminder = datetime.combine(now.date(), reminder_time)
            next_month = now.month + 1 if now.month < 12 else 1
            year = now.year if now.month < 12 else now.year + 1
            next_reminder = next_reminder.replace(month=next_month, year=year)
        
        else:  # one-time
            next_reminder = datetime.combine(now.date(), reminder_time)
            if next_reminder <= now:
                next_reminder += timedelta(days=1)
        
        return next_reminder