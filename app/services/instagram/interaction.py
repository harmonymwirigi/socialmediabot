#social-media-bot/app/services/instagram/interaction.py

from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import logging
import time
import random
import os
import shutil
from typing import List, Dict, Any
from .browser import InstagramBrowser

class FixedInstagramInteractionService:
    def __init__(self, account_service):
        self.account_service = account_service
        self.logger = logging.getLogger(__name__)
        self.progress_callback = None
        self.driver_lock = threading.Lock()
        self.browser = InstagramBrowser()
        
        self.delays = {
            'between_comments': (5, 10),
            'between_accounts': (3, 5)
        }
    def _distribute_comments(self, comments, valid_accounts):
        """Distribute comments among accounts evenly"""
        if not valid_accounts:
            raise Exception("No valid accounts available")
            
        comment_distribution = []
        num_accounts = len(valid_accounts)
        
        # Calculate minimum comments per account
        base_comments_per_account = len(comments) // num_accounts
        extra_comments = len(comments) % num_accounts
        
        current_comment_index = 0
        
        # Distribute comments among accounts
        for i, account in enumerate(valid_accounts):
            # Calculate how many comments this account should handle
            num_comments = base_comments_per_account
            if i < extra_comments:  # Distribute remaining comments
                num_comments += 1
                
            if num_comments > 0:
                account_comments = comments[current_comment_index:current_comment_index + num_comments]
                comment_distribution.append({
                    'account': account,
                    'comments': account_comments
                })
                current_comment_index += num_comments
        
        return comment_distribution

    def set_progress_callback(self, callback):
        """Set callback for UI progress updates"""
        self.progress_callback = callback

    def update_progress(self, current, total):
        """Update progress in UI"""
        if self.progress_callback:
            progress = (current / total) * 100
            self.progress_callback(progress)

    def _cleanup_chrome_driver(self):
        """Clean up ChromeDriver files before creating new instance"""
        try:
            driver_path = os.path.expanduser('~\\appdata\\roaming\\undetected_chromedriver')
            if os.path.exists(driver_path):
                shutil.rmtree(driver_path)
                time.sleep(1)  # Give OS time to complete deletion
        except Exception as e:
            self.logger.warning(f"Failed to cleanup ChromeDriver: {str(e)}")

    def _create_browser_instance(self):
        """Create a new browser instance with proper cleanup"""
        with self.driver_lock:
            self._cleanup_chrome_driver()
            return InstagramBrowser()

    def _comment_with_account(self, post_url: str, comments: List[str], 
                            account: tuple, progress_queue: queue.Queue) -> List[Dict]:
        """Handle commenting for a single account"""
        username, encrypted_password = account
        results = []
        driver = None
        browser = None
        
        try:
            # Create browser instance
            self.logger.info(f"Creating browser instance for {username}")
            browser = self._create_browser_instance()
            
            # Decrypt password and login
            password = self.account_service.decrypt_password(encrypted_password)
            self.logger.info(f"Attempting login for {username}")
            
            driver = browser.login(username, password)
            if not driver:
                raise Exception(f"Failed to login with account {username}")
            
            self.logger.info(f"Successfully logged in as {username}")
            time.sleep(2)  # Short pause after login
            
            # Process each comment
            for comment in comments:
                try:
                    # Navigate to post URL for each comment to ensure fresh state
                    driver.get(post_url)
                    time.sleep(3)  # Wait for page load
                    
                    success = browser.post_comment(driver, post_url, comment)
                    
                    if success:
                        self.logger.info(f"Comment posted successfully by {username}")
                        self.account_service.update_last_used(username)
                        progress_queue.put(1)
                        
                        # Add natural delay between comments
                        time.sleep(random.uniform(*self.delays['between_comments']))
                    
                    results.append({
                        'username': username,
                        'comment': comment,
                        'success': success,
                        'error': None
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error posting comment with {username}: {str(e)}")
                    results.append({
                        'username': username,
                        'comment': comment,
                        'success': False,
                        'error': str(e)
                    })
                    # Continue with next comment
                    
        except Exception as e:
            self.logger.error(f"Account process failed for {username}: {str(e)}")
            for comment in comments:
                results.append({
                    'username': username,
                    'comment': comment,
                    'success': False,
                    'error': str(e)
                })
                
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(1)  # Give time for driver to close properly
            
        return results

    def comment_on_post(self, post_url, comments):
        """Main method for commenting with improved session handling and error recovery"""
        try:
            self.logger.info(f"Starting comment operation for {len(comments)} comments")
            print(f"DEBUG: Starting comment operation for {len(comments)} comments")
            
            # Get active accounts
            accounts = self.account_service.get_active_accounts()
            print(f"DEBUG: Found {len(accounts)} active accounts from service")
            
            # Fallback: if no accounts from service, try direct DB query
            if not accounts:
                print("DEBUG: No accounts from service, trying direct DB query")
                from app.models import InstagramAccount
                db_accounts = InstagramAccount.query.all()
                
                # Use all accounts for testing
                accounts = []
                for account in db_accounts:
                    try:
                        print(f"DEBUG: Adding account {account.username}")
                        accounts.append((account.username, account.password_encrypted))
                    except Exception as e:
                        print(f"DEBUG: Error adding account {account.username}: {str(e)}")
            
            if not accounts:
                raise Exception("No active accounts found")
            
            self.logger.info(f"Found {len(accounts)} active accounts")
            print(f"DEBUG: Using {len(accounts)} accounts: {[a[0] for a in accounts]}")
            
            self.logger.info(f"Found {len(accounts)} active accounts")
            print(f"DEBUG: Found {len(accounts)} active accounts: {[a[0] for a in accounts]}")  # Debug print
            
            
            # Distribute comments among accounts
            comment_distribution = self._distribute_comments(comments, accounts)
            
            # Setup progress tracking
            total_comments = len(comments)
            completed_comments = 0
            all_results = []
            
            # Process each account's comments
            for distribution in comment_distribution:
                account = distribution['account']
                account_comments = distribution['comments']
                username, encrypted_password = account
                
                self.logger.info(f"Processing {len(account_comments)} comments for {username}")
                driver = None
                
                try:
                    # Decrypt password with better error handling
                    try:
                        print(f"DEBUG: Attempting to decrypt password for {username}")
                        password = self.account_service.decrypt_password(encrypted_password)
                        print(f"DEBUG: Password decryption successful")
                    except Exception as e:
                        error_msg = f"Password decryption failed for {username}: {str(e)}"
                        self.logger.error(error_msg)
                        print(f"DEBUG ERROR: {error_msg}")
                        
                        # Skip this account and continue with others
                        all_results.extend([
                            {
                                'username': username,
                                'comment': comment,
                                'success': False,
                                'error': error_msg
                            } for comment in account_comments
                        ])
                        continue
                    session_created = False
                    session_attempts = 0
                    max_session_attempts = 2
                    
                    while not session_created and session_attempts < max_session_attempts:
                        try:
                            session_attempts += 1
                            
                            if self.browser._check_cookies_exist(username):
                                # Try to create session with existing cookies
                                self.logger.info(f"Attempting to create session with existing cookies for {username}")
                                driver = self.browser.create_comment_session(username, post_url)
                                
                                # Verify session is valid
                                if self.browser._verify_login(driver):
                                    session_created = True
                                    self.logger.info(f"Successfully created session with cookies for {username}")
                                else:
                                    raise Exception("Session verification failed")
                            else:
                                # No cookies exist, perform fresh login
                                self.logger.info(f"No cookies found for {username}, performing fresh login")
                                driver = self.browser.login(username, password)
                                session_created = True
                                
                        except Exception as e:
                            self.logger.warning(f"Session attempt {session_attempts} failed for {username}: {str(e)}")
                            if driver:
                                try:
                                    driver.quit()
                                except:
                                    pass
                                driver = None
                                
                            # On first failure with cookies, try fresh login
                            if session_attempts == 1 and self.browser._check_cookies_exist(username):
                                self.logger.info(f"Cookie session failed for {username}, attempting fresh login")
                                try:
                                    driver = self.browser.login(username, password)
                                    session_created = True
                                except Exception as login_error:
                                    self.logger.error(f"Fresh login failed for {username}: {str(login_error)}")
                                    raise
                    
                    if not session_created:
                        raise Exception(f"Failed to create valid session for {username} after {max_session_attempts} attempts")
                    
                    # Process comments for this account
                    for comment in account_comments:
                        try:
                            # Verify we're on the correct post page
                            current_url = self.browser._normalize_url(driver.current_url)
                            expected_url = self.browser._normalize_url(post_url)
                            
                            if current_url != expected_url:
                                driver.get(post_url)
                                time.sleep(3)  # Wait for page load
                            
                            # Check if comments are enabled
                            if not self.browser._check_comments_enabled(driver):
                                raise Exception("Comments are disabled on this post")
                            
                            # Attempt to post comment
                            success = self.browser.post_comment(driver, post_url, comment)
                            
                            if success:
                                self.logger.info(f"Successfully posted comment with {username}")
                                self.account_service.update_last_used(username)
                                completed_comments += 1
                                
                                # Update progress
                                if self.progress_callback:
                                    self.progress_callback(completed_comments / total_comments * 100)
                                
                                # Save result
                                all_results.append({
                                    'username': username,
                                    'comment': comment,
                                    'success': True,
                                    'error': None
                                })
                                
                                # Add natural delay between comments
                                time.sleep(random.uniform(*self.delays['between_comments']))
                            else:
                                raise Exception("Comment was not verified as posted")
                                
                        except Exception as e:
                            self.logger.error(f"Failed to post comment with {username}: {str(e)}")
                            all_results.append({
                                'username': username,
                                'comment': comment,
                                'success': False,
                                'error': str(e)
                            })
                            
                            # If we get a login-related error, try to recover session
                            if "login" in driver.current_url:
                                self.logger.info(f"Detected login redirect for {username}, attempting session recovery")
                                try:
                                    driver.quit()
                                    driver = self.browser.login(username, password)
                                except:
                                    break  # Break comment loop if login recovery fails
                    
                except Exception as e:
                    self.logger.error(f"Account process failed for {username}: {str(e)}")
                    # Record failure for all remaining comments
                    for comment in account_comments:
                        all_results.append({
                            'username': username,
                            'comment': comment,
                            'success': False,
                            'error': str(e)
                        })
                        
                finally:
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                        time.sleep(1)  # Allow time for cleanup
                    
                    # Add delay between accounts
                    time.sleep(random.uniform(*self.delays['between_accounts']))
            
            # Calculate success rate
            success_count = len([r for r in all_results if r['success']])
            success_rate = (success_count / len(comments)) * 100
            self.logger.info(f"Comment operation completed. Success rate: {success_rate:.2f}%")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Comment operation failed: {str(e)}")
            raise