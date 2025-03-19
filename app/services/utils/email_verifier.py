# app/services/utils/email_verifier.py
import logging
import time
import re
import random
import string
import requests
from datetime import datetime, timedelta

class EmailVerifier:
    """
    Service for handling email verification codes
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_email_domains = [
            'tempmail.com',
            'temp-mail.org',
            'mailinator.com',
            'guerrillamail.com',
            'inbox.lv',
            'trashmail.com'
        ]
        self.active_emails = {}
    
    def generate_temp_email(self):
        """
        Generate a temporary email address
        
        Returns:
            str: A temporary email address
        """
        try:
            # Create a random username
            username_length = random.randint(8, 12)
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=username_length))
            
            # Select a random domain
            domain = random.choice(self.temp_email_domains)
            
            email = f"{username}@{domain}"
            self.logger.info(f"Generated temporary email: {email}")
            
            # Store in active emails
            self.active_emails[email] = {
                'created_at': datetime.now(),
                'last_checked': None,
                'verification_code': None
            }
            
            return email
        except Exception as e:
            self.logger.error(f"Failed to generate temporary email: {str(e)}")
            return None
    
    def get_verification_code(self, email, max_wait=60, check_interval=5):
        """
        Get verification code from email
        
        In a real implementation, this would connect to an email API
        For this demo, we'll simulate it with random codes
        
        Args:
            email (str): Email address to check
            max_wait (int): Maximum time to wait in seconds
            check_interval (int): Time between checks in seconds
            
        Returns:
            str: Verification code or None if not found
        """
        try:
            # Check if email is in our active list
            if email not in self.active_emails:
                self.active_emails[email] = {
                    'created_at': datetime.now(),
                    'last_checked': None,
                    'verification_code': None
                }
            
            # Update last checked time
            self.active_emails[email]['last_checked'] = datetime.now()
            
            # For demo purposes, generate a random code after a delay
            # In a real implementation, this would check an email API
            start_time = time.time()
            elapsed_time = 0
            
            while elapsed_time < max_wait:
                # Simulate checking email
                self.logger.info(f"Checking for verification code in {email}...")
                
                # Randomly decide if we found a code (higher chance as time passes)
                chance = min(0.1 + (elapsed_time / max_wait), 0.9)
                if random.random() < chance:
                    # Generate a 6-digit code
                    code = ''.join(random.choices(string.digits, k=6))
                    self.active_emails[email]['verification_code'] = code
                    self.logger.info(f"Found verification code: {code}")
                    return code
                
                # Wait before checking again
                time.sleep(check_interval)
                elapsed_time = time.time() - start_time
            
            self.logger.warning(f"No verification code found for {email} after {max_wait}s")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting verification code: {str(e)}")
            return None
    
    def verify_email(self, email):
        """
        Verify if an email address is valid
        
        Args:
            email (str): Email address to verify
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        # Basic email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return False
        
        # Check if it's a disposable email
        domain = email.split('@')[1]
        if domain in self.temp_email_domains:
            return True
        
        # In a real implementation, you might use an email verification API
        # For this demo, we'll just return True
        return True