# app/database.py

import sqlite3
from contextlib import contextmanager
import datetime

class Database:
    def __init__(self, db_name='instagram_bot.db'):
        self.db_name = db_name
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create accounts table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                encrypted_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                creation_date TIMESTAMP,
                creation_ip TEXT,
                email TEXT,
                phone TEXT,
                verified BOOLEAN DEFAULT 0,
                profile_completed BOOLEAN DEFAULT 0
            )
            ''')
            
            # Create account_creation_logs table for tracking creation attempts
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_creation_logs (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                success BOOLEAN,
                error_message TEXT,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                proxy_used TEXT,
                verification_required BOOLEAN DEFAULT 0,
                verification_type TEXT,
                captcha_required BOOLEAN DEFAULT 0
            )
            ''')
            
            conn.commit()
    
    def execute(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def fetch_all(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def add_account_with_details(self, username, encrypted_password, email=None, phone=None, creation_ip=None):
        """Add an account with additional details"""
        return self.execute(
            '''INSERT INTO accounts 
               (username, encrypted_password, email, phone, creation_ip, creation_date, verified, profile_completed) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (username, encrypted_password, email, phone, creation_ip, datetime.datetime.now(), 0, 0)
        )
    
    def update_account_verification(self, username, verified=True):
        """Update account verification status"""
        return self.execute(
            'UPDATE accounts SET verified = ? WHERE username = ?',
            (verified, username)
        )
    
    def update_account_profile_status(self, username, completed=True):
        """Update account profile completion status"""
        return self.execute(
            'UPDATE accounts SET profile_completed = ? WHERE username = ?',
            (completed, username)
        )
    
    def log_creation_attempt(self, username, email, success, error_message=None, 
                           ip_address=None, proxy_used=None, verification_required=False,
                           verification_type=None, captcha_required=False):
        """Log an account creation attempt"""
        return self.execute(
            '''INSERT INTO account_creation_logs 
               (username, email, success, error_message, ip_address, proxy_used, 
                verification_required, verification_type, captcha_required) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (username, email, success, error_message, ip_address, proxy_used,
             verification_required, verification_type, captcha_required)
        )
    
    def get_creation_stats(self, days=30):
        """Get account creation statistics for the last N days"""
        date_threshold = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        stats = {}
        
        # Get total attempts
        stats['total_attempts'] = self.fetch_one(
            '''SELECT COUNT(*) FROM account_creation_logs 
               WHERE creation_date >= ?''',
            (date_threshold,)
        )[0]
        
        # Get successful attempts
        stats['successful'] = self.fetch_one(
            '''SELECT COUNT(*) FROM account_creation_logs 
               WHERE success = 1 AND creation_date >= ?''',
            (date_threshold,)
        )[0]
        
        # Get verification requirements
        stats['verification_required'] = self.fetch_one(
            '''SELECT COUNT(*) FROM account_creation_logs 
               WHERE verification_required = 1 AND creation_date >= ?''',
            (date_threshold,)
        )[0]
        
        # Get verification types breakdown
        verification_types = self.fetch_all(
            '''SELECT verification_type, COUNT(*) FROM account_creation_logs 
               WHERE verification_required = 1 AND creation_date >= ?
               GROUP BY verification_type''',
            (date_threshold,)
        )
        stats['verification_types'] = {vtype: count for vtype, count in verification_types}
        
        # Get captcha requirements
        stats['captcha_required'] = self.fetch_one(
            '''SELECT COUNT(*) FROM account_creation_logs 
               WHERE captcha_required = 1 AND creation_date >= ?''',
            (date_threshold,)
        )[0]
        
        # Get error breakdown
        error_types = self.fetch_all(
            '''SELECT error_message, COUNT(*) FROM account_creation_logs 
               WHERE success = 0 AND creation_date >= ?
               GROUP BY error_message''',
            (date_threshold,)
        )
        stats['error_types'] = {err: count for err, count in error_types}
        
        return stats