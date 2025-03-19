# app/utils/email_verifier.py

import time
import re
import logging
import threading
import requests
import imaplib
import email
from email.header import decode_header
import poplib
from datetime import datetime, timedelta

class EmailVerifier:
    """
    Handles email verification codes for account creation
    Supports both temporary/disposable email services and IMAP/POP3 accounts
    """
    
    def __init__(self, temp_email_service=None, imap_settings=None):
        self.logger = logging.getLogger(__name__)
        self.temp_email_service = temp_email_service
        self.imap_settings = imap_settings
        
        # Map of temp email addresses to their access tokens or IDs
        self.temp_email_map = {}
        self.lock = threading.Lock()
        
        # Common verification code patterns
        self.verification_patterns = [
            r'verification code[^\d]*(\d{4,8})',
            r'confirmation code[^\d]*(\d{4,8})',
            r'security code[^\d]*(\d{4,8})',
            r'code[^\d]*(\d{4,8})',
            r'(\d{6})',  # Instagram typically uses 6-digit codes
        ]
    
    def generate_temp_email(self):
        """
        Generate a temporary/disposable email address
        
        Returns:
            str: Temporary email address
        """
        if not self.temp_email_service:
            self.logger.error("No temporary email service configured")
            return None
        
        try:
            self.logger.info("Generating temporary email address")
            
            # This would be replaced with actual API call to your temp email provider
            service_url = self.temp_email_service.get('api_url')
            api_key = self.temp_email_service.get('api_key')
            
            # Example: create email with API
            response = requests.post(
                f"{service_url}/create", 
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                email_address = data.get('email')
                access_token = data.get('access_token')
                
                # Store the access token for later retrieval
                with self.lock:
                    self.temp_email_map[email_address] = access_token
                
                self.logger.info(f"Generated temporary email: {email_address}")
                return email_address
            else:
                self.logger.error(f"Failed to generate temp email: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating temporary email: {str(e)}")
            return None
    
    def get_verification_code(self, email_address, max_wait=120, check_interval=5):
        """
        Get verification code from email inbox
        
        Args:
            email_address (str): Email address to check
            max_wait (int): Maximum time to wait in seconds
            check_interval (int): How often to check inbox in seconds
            
        Returns:
            str: Verification code or None if not found
        """
        # Determine if this is a temporary email or a regular IMAP/POP3
        is_temp_email = email_address in self.temp_email_map
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                if is_temp_email:
                    code = self._check_temp_email(email_address)
                else:
                    code = self._check_imap_email(email_address)
                
                if code:
                    self.logger.info(f"Found verification code: {code}")
                    return code
                
                # Wait before checking again
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error checking email: {str(e)}")
                time.sleep(check_interval)
        
        self.logger.warning(f"No verification code found within {max_wait} seconds")
        return None
    
    def _check_temp_email(self, email_address):
        """
        Check temporary email service for verification code
        
        Args:
            email_address (str): Temporary email address
            
        Returns:
            str: Verification code or None if not found
        """
        try:
            access_token = self.temp_email_map.get(email_address)
            if not access_token:
                self.logger.error(f"No access token found for {email_address}")
                return None
            
            service_url = self.temp_email_service.get('api_url')
            
            # Get messages
            response = requests.get(
                f"{service_url}/messages",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                self.logger.error(f"Failed to fetch messages: {response.text}")
                return None
            
            messages = response.json().get('messages', [])
            
            # Look for Instagram messages
            for message in messages:
                sender = message.get('from', '')
                subject = message.get('subject', '')
                body = message.get('body', '')
                
                # Check if this is from Instagram
                if 'instagram' in sender.lower() or 'instagram' in subject.lower():
                    self.logger.info(f"Found Instagram email: {subject}")
                    
                    # Extract verification code from body
                    code = self._extract_verification_code(body)
                    if code:
                        return code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking temporary email: {str(e)}")
            return None
    
    def _check_imap_email(self, email_address):
        """
        Check IMAP email for verification code
        
        Args:
            email_address (str): Email address to check
            
        Returns:
            str: Verification code or None if not found
        """
        if not self.imap_settings:
            self.logger.error("No IMAP settings configured")
            return None
        
        try:
            # Get settings
            imap_server = self.imap_settings.get('server')
            imap_port = self.imap_settings.get('port', 993)
            username = email_address
            password = self.imap_settings.get('password')
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
            mail.select('inbox')
            
            # Search for recent emails
            date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            result, data = mail.search(None, f'(SINCE {date})')
            
            if result != 'OK':
                self.logger.error("Failed to search emails")
                return None
            
            email_ids = data[0].split()
            
            # Check most recent emails first
            for email_id in reversed(email_ids):
                result, data = mail.fetch(email_id, '(RFC822)')
                
                if result != 'OK':
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                subject = self._decode_email_header(msg['Subject'])
                sender = self._decode_email_header(msg['From'])
                
                # Check if this is from Instagram
                if 'instagram' in sender.lower() or 'instagram' in subject.lower():
                    self.logger.info(f"Found Instagram email: {subject}")
                    
                    # Get body content
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == 'text/plain' or content_type == 'text/html':
                                charset = part.get_content_charset() or 'utf-8'
                                body += part.get_payload(decode=True).decode(charset, errors='replace')
                    else:
                        charset = msg.get_content_charset() or 'utf-8'
                        body = msg.get_payload(decode=True).decode(charset, errors='replace')
                    
                    # Extract verification code from body
                    code = self._extract_verification_code(body)
                    if code:
                        return code
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking IMAP email: {str(e)}")
            return None
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
    
    def _decode_email_header(self, header):
        """Decode email header"""
        if header is None:
            return ""
            
        decoded_header = decode_header(header)
        header_parts = []
        
        for part, encoding in decoded_header:
            if isinstance(part, bytes):
                if encoding:
                    part = part.decode(encoding)
                else:
                    part = part.decode('utf-8', errors='replace')
            header_parts.append(part)
            
        return ' '.join(header_parts)
    
    def _extract_verification_code(self, text):
        """
        Extract verification code from text
        
        Args:
            text (str): Text to search for code
            
        Returns:
            str: Verification code or None if not found
        """
        # Try each pattern
        for pattern in self.verification_patterns:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(1)
        
        return None