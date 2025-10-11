import sqlite3
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        try:
            self.conn = sqlite3.connect('expense_tracker.db', check_same_thread=False)
            self.create_tables()
            logger.info("✅ SQLite database initialized successfully!")
        except Exception as e:
            logger.error(f"❌ SQLite database initialization failed: {e}")
            raise

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                monthly_income REAL DEFAULT 0,
                currency TEXT DEFAULT 'USD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                description TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category TEXT,
                amount REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, category),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()

    def get_user(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'monthly_income': row[3],
                    'currency': row[4],
                    'created_at': row[5]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def create_user(self, user_id, username, first_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False

    def add_expense(self, user_id, amount, category, description, date=None):
        try:
            cursor = self.conn.cursor()
            expense_date = date or datetime.now()
            cursor.execute('''
                INSERT INTO expenses (user_id, amount, category, description, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, float(amount), category, description, expense_date))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding expense for user {user_id}: {e}")
            return False

    def get_user_expenses(self, user_id, month=None, year=None):
        try:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC'
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
            expenses = []
            for row in rows:
                expenses.append({
                    'id': row[0],
                    'user_id': row[1],
                    'amount': row[2],
                    'category': row[3],
                    'description': row[4],
                    'date': row[5],
                    'created_at': row[6]
                })
            return expenses
        except Exception as e:
            logger.error(f"Error getting expenses for user {user_id}: {e}")
            return []

    def set_budget(self, user_id, category, amount):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO budgets (user_id, category, amount, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, category, float(amount), datetime.now()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting budget for user {user_id}: {e}")
            return False

    def get_user_budgets(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM budgets WHERE user_id = ?', (user_id,))
            rows = cursor.fetchall()
            
            budgets = []
            for row in rows:
                budgets.append({
                    'id': row[0],
                    'user_id': row[1],
                    'category': row[2],
                    'amount': row[3],
                    'updated_at': row[4]
                })
            return budgets
        except Exception as e:
            logger.error(f"Error getting budgets for user {user_id}: {e}")
            return []

    def get_monthly_summary(self, user_id, month, year):
        try:
            cursor = self.conn.cursor()
            # SQLite date formatting for month/year extraction
            cursor.execute('''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses
                WHERE user_id = ? 
                AND strftime('%Y', date) = ? 
                AND strftime('%m', date) = ?
                GROUP BY category
            ''', (user_id, str(year), f"{month:02d}"))
            
            rows = cursor.fetchall()
            summary = []
            for row in rows:
                summary.append({
                    '_id': row[0],
                    'total': row[1] or 0,
                    'count': row[2] or 0
                })
            return summary
        except Exception as e:
            logger.error(f"Error getting monthly summary for user {user_id}: {e}")
            return []

# Initialize database
db = Database()