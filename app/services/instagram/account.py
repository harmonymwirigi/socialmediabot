# social-media-bot/app/services/instagram/account.py

import datetime
import logging
from app import db
from app.models import InstagramAccount

class InstagramAccountService:
    """Service for managing Instagram accounts using Flask-SQLAlchemy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def add_account(self, username, email=None, phone=None, creation_ip=None, user_id=None):
        """Add an account to the database"""
        try:
            # Create a new InstagramAccount object
            account = InstagramAccount(
                username=username,
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
            
            # Convert to format expected by interaction service (only return username)
            return [(account.username, None) for account in accounts]
            
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
    
    def get_accounts_with_details(self):
        """Get all accounts with detailed info"""
        try:
            accounts = InstagramAccount.query.all()
            return accounts
        except Exception as e:
            self.logger.error(f"Failed to get accounts with details: {str(e)}")
            return []
    
    def get_account_details(self, username):
        """Get detailed information for a specific account"""
        try:
            account = InstagramAccount.query.filter_by(username=username).first()
            return account
        except Exception as e:
            self.logger.error(f"Failed to get account details for {username}: {str(e)}")
            return None
    
    def log_creation_attempt(self, username, email, success, error_message=None, 
                           ip_address=None, proxy_used=None, verification_required=False,
                           verification_type=None, captcha_required=False):
        """Log an account creation attempt"""
        try:
            # This would typically be implemented with a database model
            self.logger.info(f"Account creation attempt: {username}, {email}, success: {success}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to log creation attempt: {str(e)}")
            return False
    
    def get_creation_stats(self, days=30):
        """Get account creation statistics for the last N days"""
        try:
            # This would typically be implemented with database queries
            return {
                'total_attempts': 0,
                'successful': 0,
                'verification_required': 0,
                'verification_types': {},
                'captcha_required': 0,
                'error_types': {}
            }
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