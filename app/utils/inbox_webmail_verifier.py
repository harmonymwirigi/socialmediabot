# app/utils/inbox_webmail_verifier.py

import time
import logging
import re
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class InboxWebmailVerifier:
    """
    Handles email verification for inbox.lv accounts using browser automation
    """
    
    def __init__(self, headless=True, wait_timeout=30):
        self.logger = logging.getLogger(__name__)
        self.headless = headless
        self.wait_timeout = wait_timeout
        self.driver = None
        self.lock = threading.Lock()
        
        # Verification code patterns
        self.verification_patterns = [
            r'verification code[^\d]*(\d{4,8})',
            r'confirmation code[^\d]*(\d{4,8})',
            r'security code[^\d]*(\d{6})',
            r'instagram code[^\d]*(\d{4,8})',
            r'code is[^\d]*(\d{6})',
            r'code:[^\d]*(\d{6})'
        ]
    
    def _create_driver(self):
        """Create a browser driver instance"""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
            
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-notifications')
            
            # Create a new driver
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.wait_timeout)
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create driver: {str(e)}")
            raise
    
    def login(self, email, password):
        """
        Login to inbox.lv webmail
        
        Args:
            email (str): Inbox.lv email address
            password (str): Inbox.lv password
            
        Returns:
            bool: Whether login was successful
        """
        with self.lock:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            try:
                self.logger.info(f"Logging in to inbox.lv as {email}")
                
                # Create a new driver
                self.driver = self._create_driver()
                
                # Navigate to inbox.lv
                self.driver.get('https://www.inbox.lv/')
                
                # Wait for login form to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'imapuser'))
                )
                
                # Enter email
                username_field = self.driver.find_element(By.ID, 'imapuser')
                username_field.clear()
                username_field.send_keys(email)
                
                # Enter password
                password_field = self.driver.find_element(By.ID, 'pass')
                password_field.clear()
                password_field.send_keys(password)
                
                # Click login button
                login_button = self.driver.find_element(By.NAME, 'go')
                login_button.click()
                
                # Wait for inbox to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.mail-list-item, .mail-list'))
                )
                
                self.logger.info(f"Successfully logged in to inbox.lv as {email}")
                return True
                
            except TimeoutException:
                self.logger.error(f"Timeout while trying to log in to inbox.lv as {email}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                return False
                
            except Exception as e:
                self.logger.error(f"Failed to log in to inbox.lv: {str(e)}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                return False
    
    def check_for_verification_code(self, max_emails=10):
        """
        Check inbox for verification codes in existing emails
        
        Args:
            max_emails (int): Maximum number of emails to check
            
        Returns:
            str: Verification code or None if not found
        """
        if not self.driver:
            self.logger.error("Not logged in to inbox.lv")
            return None
        
        try:
            self.logger.info("Checking inbox for verification emails")
            
            # Check if inbox is empty
            empty_messages = self.driver.find_elements(By.CSS_SELECTOR, '.empty-folder')
            if empty_messages and "No messages" in empty_messages[0].text:
                self.logger.info("Inbox is empty")
                return None
            
            # Find all emails
            emails = self.driver.find_elements(By.CSS_SELECTOR, '.mail-list-item')
            
            if not emails:
                self.logger.info("No emails found in inbox")
                return None
            
            self.logger.info(f"Found {len(emails)} emails in inbox")
            
            # Check the most recent emails (limited by max_emails)
            for i, email in enumerate(emails[:max_emails]):
                try:
                    sender = email.find_element(By.CSS_SELECTOR, '.from').text
                    subject = email.find_element(By.CSS_SELECTOR, '.subject').text
                    
                    self.logger.debug(f"Email {i+1}: From '{sender}', Subject: '{subject}'")
                    
                    # Check if this is an Instagram email
                    if 'instagram' in sender.lower() or 'instagram' in subject.lower():
                        self.logger.info(f"Found Instagram email: '{subject}'")
                        
                        # Click to open the email
                        email.click()
                        
                        # Wait for email content to load
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.message-body'))
                        )
                        
                        # Get email content
                        content_element = self.driver.find_element(By.CSS_SELECTOR, '.message-body')
                        content = content_element.text
                        
                        # Try to find verification code
                        for pattern in self.verification_patterns:
                            matches = re.search(pattern, content, re.IGNORECASE)
                            if matches:
                                code = matches.group(1)
                                self.logger.info(f"Found verification code: {code}")
                                return code
                        
                        # Go back to inbox
                        inbox_link = self.driver.find_element(By.LINK_TEXT, 'Inbox')
                        inbox_link.click()
                        
                        # Wait for inbox to load again
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.mail-list-item, .mail-list'))
                        )
                        
                except Exception as e:
                    self.logger.warning(f"Error checking email {i+1}: {str(e)}")
                    # Try to go back to inbox view if something went wrong
                    try:
                        self.driver.get('https://www.inbox.lv/')
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '.mail-list-item, .mail-list'))
                        )
                    except:
                        pass
                    continue
            
            self.logger.info("No verification code found in existing emails")
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for verification code: {str(e)}")
            return None
    
    def wait_for_verification_code(self, timeout=300, check_interval=10):
        """
        Wait for a new verification code to arrive
        
        Args:
            timeout (int): Maximum time to wait in seconds
            check_interval (int): How often to check inbox
            
        Returns:
            str: Verification code or None if not found
        """
        if not self.driver:
            self.logger.error("Not logged in to inbox.lv")
            return None
        
        try:
            self.logger.info(f"Waiting for verification code (timeout: {timeout}s)")
            
            # First check existing emails
            code = self.check_for_verification_code()
            if code:
                return code
            
            # If no code found, start waiting for new emails
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Refresh the page
                self.driver.refresh()
                
                # Wait for inbox to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.mail-list-item, .mail-list'))
                )
                
                # Check for verification code
                code = self.check_for_verification_code(max_emails=3)  # Only check the top few emails
                if code:
                    return code
                
                # Calculate remaining time
                elapsed = int(time.time() - start_time)
                remaining = timeout - elapsed
                
                self.logger.info(f"No verification code found yet. {remaining}s remaining.")
                
                # Wait before checking again
                time.sleep(check_interval)
            
            self.logger.warning(f"Timeout reached ({timeout}s). No verification code found.")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for verification code: {str(e)}")
            return None
    
    def close(self):
        """Close the browser and clean up"""
        with self.lock:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                self.logger.info("Browser closed")
    
    def __del__(self):
        """Destructor to ensure browser is closed"""
        self.close()


# Test function to verify the class works correctly
def test_inbox_webmail_verifier(email, password, wait_for_code=False):
    """
    Test the InboxWebmailVerifier class
    
    Args:
        email (str): Inbox.lv email address
        password (str): Inbox.lv password
        wait_for_code (bool): Whether to wait for a verification code
    """
    verifier = InboxWebmailVerifier(headless=False)  # Set headless=False to see the browser
    
    try:
        # Login
        if not verifier.login(email, password):
            print("Failed to log in to inbox.lv")
            return
        
        print("Successfully logged in to inbox.lv")
        
        if wait_for_code:
            # Wait for verification code
            print("Waiting for verification code...")
            code = verifier.wait_for_verification_code(timeout=120)  # 2 minutes timeout
            
            if code:
                print(f"Found verification code: {code}")
            else:
                print("No verification code found")
        else:
            # Check for existing verification code
            print("Checking for existing verification code...")
            code = verifier.check_for_verification_code()
            
            if code:
                print(f"Found verification code: {code}")
            else:
                print("No verification code found in existing emails")
    
    finally:
        # Clean up
        verifier.close()


if __name__ == "__main__":
    import getpass
    
    # Get credentials
    email = input("Enter your inbox.lv email address: ")
    password = getpass.getpass("Enter your password: ")
    
    # Ask if user wants to wait for verification code
    wait_response = input("Wait for verification code to arrive? (y/n): ").lower()
    wait_for_code = wait_response.startswith('y')
    
    # Run the test
    test_inbox_webmail_verifier(email, password, wait_for_code)