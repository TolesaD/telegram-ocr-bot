from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime, timedelta
import logging
import ssl
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        try:
            # SSL workaround for Python 3.11
            self.client = MongoClient(
                Config.MONGODB_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,  # Bypass SSL verification
                serverSelectionTimeoutMS=10000
            )
            self.db = self.client[Config.DATABASE_NAME]
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.client = None
            self.db = None
    
    def get_collection(self, name):
        if self.db is None:
            return None
        return self.db[name]
    
    def close(self):
        if self.client:
            self.client.close()

class ReminderManager:
    def __init__(self):
        self.db = Database()
        self.reminders = self.db.get_collection('reminders') if self.db.db else None
        if self.reminders is None:
            logger.warning("⚠️ Running without database - reminders won't be saved")
        
    def create_reminder(self, user_id, chat_id, time, message, recurrence=None):
        if self.reminders is None:
            logger.error("❌ No database connection - reminder not saved")
            return "no_database"
            
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
        try:
            result = self.reminders.insert_one(reminder)
            logger.info(f"✅ Reminder created for user {user_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Failed to create reminder: {e}")
            return "error"
    
    def get_user_reminders(self, user_id):
        if self.reminders is None:
            return []
        try:
            reminders = list(self.reminders.find({
                'user_id': user_id,
                'active': True
            }).sort('next_reminder', 1))
            return reminders
        except Exception as e:
            logger.error(f"❌ Failed to get user reminders: {e}")
            return []
    
    def get_due_reminders(self):
        if self.reminders is None:
            return []
        try:
            return list(self.reminders.find({
                'next_reminder': {'$lte': datetime.utcnow()},
                'active': True
            }))
        except Exception as e:
            logger.error(f"❌ Failed to get due reminders: {e}")
            return []
    
    def cancel_reminder(self, reminder_id, user_id):
        if self.reminders is None:
            return False
        from bson.objectid import ObjectId
        try:
            result = self.reminders.update_one(
                {'_id': ObjectId(reminder_id), 'user_id': user_id},
                {'$set': {'active': False}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to cancel reminder: {e}")
            return False
    
    def update_next_reminder(self, reminder_id):
        if self.reminders is None:
            return
        from bson.objectid import ObjectId
        try:
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
        except Exception as e:
            logger.error(f"❌ Failed to update next reminder: {e}")
    
    def _calculate_next_reminder(self, time_str, recurrence):
        now = datetime.utcnow()
        try:
            reminder_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            reminder_time = now.time()
        
        if recurrence == 'daily':
            next_reminder = datetime.combine(now.date(), reminder_time)
            if next_reminder <= now:
                next_reminder += timedelta(days=1)
        elif recurrence == 'weekly':
            next_reminder = datetime.combine(now.date(), reminder_time)
            days_ahead = 6 - now.weekday()
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