# social-media-bot/app/services/instagram/account.py

from cryptography.fernet import Fernet
import os
import datetime
import logging
from app import db  # Import SQLAlchemy db
from app.models import InstagramAccount  


class InstagramAccountService:
    """Service for managing Instagram accounts using Flask-SQLAlchemy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption for secure password storage"""
        try:
            # Create key if it doesn't exist
            if not os.path.exists('secret.key'):
                print("Creating new encryption key")
                key = Fernet.generate_key()
                with open('secret.key', 'wb') as key_file:
                    key_file.write(key)
            
            # Read the key
            with open('secret.key', 'rb') as key_file:
                self.key = key_file.read()
            
            self.fernet = Fernet(self.key)
            print("Encryption initialized successfully")
        except Exception as e:
            print(f"Error initializing encryption: {str(e)}")
            raise


    def decrypt_password(self, encrypted_password):
        """Decrypt a password for use in automation"""
        try:
            # Handle string vs bytes
            if isinstance(encrypted_password, str):
                try:
                    import base64
                    encrypted_password = base64.b64decode(encrypted_password)
                except:
                    encrypted_password = encrypted_password.encode()
            
            decrypted = self.fernet.decrypt(encrypted_password)
            return decrypted.decode()
        except Exception as e:
            print(f"Failed to decrypt password: {str(e)}")
            raise
    
    def add_account(self, username, password, email=None, phone=None, creation_ip=None, user_id=None):
        """Add an account to the database with encrypted password"""
        try:
            encrypted_password = self.fernet.encrypt(password.encode())
            
            # Create a new InstagramAccount object
            account = InstagramAccount(
                username=username, 
                password_encrypted=encrypted_password,
                email=email,
                phone=phone,
                creation_ip=creation_ip,
                is_active=True,
                user_id=user_id or 1,  # Default to user_id 1 if not provided
                creation_date=datetime.datetime.utcnow()
            )
            
            # Add and commit to database
            db.session.add(account)
            db.session.commit()
            
            return account.id
        except Exception as e:
            self.logger.error(f"Failed to add account {username}: {str(e)}")
            db.session.rollback()
            raise
    
    def update_account_status(self, username, is_active):
        """Update account active status"""
        try:
            account = InstagramAccount.query.filter_by(username=username).first()
            if account:
                account.is_active = is_active
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update account status: {str(e)}")
            db.session.rollback()
            return False
    
    def update_account_verification(self, username, verified=True):
        """Update account verification status"""
        try:
            account = InstagramAccount.query.filter_by(username=username).first()
            if account:
                account.verified = verified
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update account verification: {str(e)}")
            db.session.rollback()
            return False
    
    def get_accounts(self):
        """Get all accounts with basic info"""
        try:
            accounts = InstagramAccount.query.all()
            return [(account.username, account.is_active, account.last_used) 
                    for account in accounts]
        except Exception as e:
            self.logger.error(f"Failed to get accounts: {str(e)}")
            return []
    
    def get_active_accounts(self):
        """Get active accounts for automation"""
        try:
            # Debug statement
            print("DEBUG: Fetching active accounts using SQLAlchemy")
            
            # Query active accounts
            accounts = InstagramAccount.query.filter_by(is_active=True).all()
            
            print(f"DEBUG: Found {len(accounts)} accounts with is_active=True")
            
            # If no accounts found, try all accounts
            if not accounts:
                print("DEBUG: No active accounts found, trying all accounts")
                accounts = InstagramAccount.query.all()
                print(f"DEBUG: Found {len(accounts)} total accounts")
            
            # Convert to format expected by interaction service
            return [(account.username, account.password_encrypted) for account in accounts]
            
        except Exception as e:
            print(f"DEBUG ERROR: Failed to get active accounts: {str(e)}")
            return []
    
    def update_last_used(self, username):
        """Update the last used timestamp for an account"""
        try:
            account = InstagramAccount.query.filter_by(username=username).first()
            if account:
                account.last_used = datetime.datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update last_used: {str(e)}")
            db.session.rollback()
            return False
    
    def change_password(self, username, new_password):
        """Update an account's password"""
        try:
            account = InstagramAccount.query.filter_by(username=username).first()
            if account:
                account.password_encrypted = self.fernet.encrypt(new_password.encode())
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to change password for {username}: {str(e)}")
            db.session.rollback()
            raise
    
    def delete_account(self, username):
        """Remove an account from the database"""
        try:
            account = InstagramAccount.query.filter_by(username=username).first()
            if account:
                db.session.delete(account)
                db.session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete account {username}: {str(e)}")
            db.session.rollback()
            raise
    
    def get_account_count(self):
        """Get total number of accounts in database"""
        try:
            return InstagramAccount.query.count()
        except Exception as e:
            self.logger.error(f"Failed to get account count: {str(e)}")
            return 0

    def decrypt_password(self, encrypted_password):
        """Decrypt a password for use in automation"""
        try:
            # Handle string vs bytes
            if isinstance(encrypted_password, str):
                try:
                    import base64
                    encrypted_password = base64.b64decode(encrypted_password)
                except:
                    encrypted_password = encrypted_password.encode()
            
            decrypted = self.fernet.decrypt(encrypted_password)
            return decrypted.decode()
        except Exception as e:
            print(f"Failed to decrypt password: {str(e)}")
            raise
    
   
    
    
   
    
    def get_accounts_with_details(self):
        """Get all accounts with detailed info"""
        return self.db.fetch_all('''
            SELECT username, is_active, last_used, email, phone, 
                   verified, profile_completed, creation_date 
            FROM accounts
        ''')
    
   
    
    def get_account_details(self, username):
        """Get detailed information for a specific account"""
        return self.db.fetch_one(
            '''SELECT username, is_active, last_used, email, phone, 
                    verified, profile_completed, creation_date, creation_ip
               FROM accounts WHERE username = ?''',
            (username,)
        )
    
    
    
    def log_creation_attempt(self, username, email, success, error_message=None, 
                           ip_address=None, proxy_used=None, verification_required=False,
                           verification_type=None, captcha_required=False):
        """Log an account creation attempt"""
        try:
            return self.db.log_creation_attempt(
                username, email, success, error_message, ip_address, proxy_used,
                verification_required, verification_type, captcha_required
            )
        except Exception as e:
            self.logger.error(f"Failed to log creation attempt: {str(e)}")
    
    def get_creation_stats(self, days=30):
        """Get account creation statistics for the last N days"""
        try:
            return self.db.get_creation_stats(days)
        except Exception as e:
            self.logger.error(f"Failed to get creation stats: {str(e)}")
            return {
                'total_attempts': 0,
                'successful': 0,
                'verification_required': 0,
                'verification_types': {},
                'captcha_required': 0,
                'error_types': {}
            }
    
    
    
    
   
   