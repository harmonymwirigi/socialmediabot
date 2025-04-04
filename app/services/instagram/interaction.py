# social-media-bot/app/services/instagram/interaction.py

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
                            username: str, progress_queue: queue.Queue) -> List[Dict]:
        """Handle commenting for a single account"""
        results = []
        driver = None
        browser = None
        
        try:
            # Create browser instance
            self.logger.info(f"Creating browser instance for {username}")
            browser = self._create_browser_instance()
            
            # First try using stored cookies
            self.logger.info(f"Attempting to create session with cookies for {username}")
            
            # A flag to track if we need manual intervention
            manual_login_needed = False
            
            try:
                # Check if cookies exist and create a session
                has_cookies = browser._check_cookies_exist(username)
                
                if has_cookies:
                    self.logger.info(f"Found cookies for {username}, creating cookie-based session")
                    driver = browser.create_comment_session(username, post_url)
                    
                    # Check if session is valid
                    if "login" in driver.current_url:
                        self.logger.info(f"Cookie session failed for {username}, manual login required")
                        manual_login_needed = True
                    else:
                        self.logger.info(f"Successfully created cookie-based session for {username}")
                else:
                    self.logger.info(f"No cookies found for {username}, manual login required")
                    manual_login_needed = True
            except Exception as e:
                self.logger.error(f"Error with cookie session for {username}: {str(e)}")
                manual_login_needed = True
                
            # If cookies failed or don't exist, initiate manual login
            if manual_login_needed:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = None
                
                self.logger.info(f"Starting manual login for {username}")
                
                # Inform the user they need to manually log in
                print(f"⚠️ Manual login required for account {username}")
                print("Please login to the Instagram account when the browser opens")
                
                # Start manual login process
                manual_login_success = browser.initiate_manual_login(username)
                
                if not manual_login_success:
                    raise Exception(f"Manual login failed or abandoned for {username}")
                
                # After successful manual login, create a new session for commenting
                driver = browser.create_comment_session(username, post_url)
            
            if not driver:
                raise Exception(f"Failed to create valid session for {username}")
            
            self.logger.info(f"Successfully established session for {username}")
            time.sleep(2)  # Short pause after session creation
            
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
            
        return result

    def comment_on_post(self, post_url, comments):
        """Main method for commenting with cookie-based authentication and manual login fallback"""
        try:
            self.logger.info(f"Starting comment operation for {len(comments)} comments")
            print(f"DEBUG: Starting comment operation for {len(comments)} comments")
            
            # Get active accounts
            accounts = self.account_service.get_active_accounts()
            print(f"DEBUG: Found {len(accounts)} active accounts from service")
            
            # Filter out unnecessary password information
            accounts = [username for username, _ in accounts]
            
            # Fallback: if no accounts from service, try direct DB query
            if not accounts:
                print("DEBUG: No accounts from service, trying direct DB query")
                from app.models import InstagramAccount
                db_accounts = InstagramAccount.query.filter_by(is_active=True).all()
                
                # Use all accounts for testing
                accounts = []
                for account in db_accounts:
                    try:
                        print(f"DEBUG: Adding account {account.username}")
                        accounts.append(account.username)
                    except Exception as e:
                        print(f"DEBUG: Error adding account {account.username}: {str(e)}")
            
            if not accounts:
                raise Exception("No active accounts found")
            
            self.logger.info(f"Found {len(accounts)} active accounts")
            print(f"DEBUG: Using {len(accounts)} accounts: {accounts}")
            
            # Distribute comments among accounts
            comment_distribution = self._distribute_comments(comments, accounts)
            
            # Setup progress tracking
            total_comments = len(comments)
            completed_comments = 0
            all_results = []
            
            # Setup threading for parallel processing
            progress_queue = queue.Queue()
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_account = {}
                
                # Submit tasks for each account
                for distribution in comment_distribution:
                    username = distribution['account']
                    account_comments = distribution['comments']
                    
                    future = executor.submit(
                        self._comment_with_account, 
                        post_url, 
                        account_comments, 
                        username, 
                        progress_queue
                    )
                    future_to_account[future] = username
                
                # Process results as they complete
                for future in future_to_account:
                    try:
                        results = future.result()
                        all_results.extend(results)
                        
                        # Update progress based on queue
                        while not progress_queue.empty():
                            progress_queue.get()
                            completed_comments += 1
                            self.update_progress(completed_comments, total_comments)
                    except Exception as e:
                        self.logger.error(f"Error in thread: {str(e)}")
            
            # Calculate success rate
            success_count = len([r for r in all_results if r['success']])
            success_rate = (success_count / len(comments)) * 100 if comments else 0
            self.logger.info(f"Comment operation completed. Success rate: {success_rate:.2f}%")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Comment operation failed: {str(e)}")
            raise

    
    def _follow_with_account(self, profile_url: str, username: str, progress_queue: queue.Queue) -> dict:
        """Handle following a profile with a single account
        
        Args:
            profile_url: URL of the Instagram profile to follow
            username: Instagram username to use for following
            progress_queue: Queue for tracking progress
            
        Returns:
            dict: Result information
        """
        result = {
            'username': username,
            'target_profile': profile_url,
            'success': False,
            'error': None
        }
        
        driver = None
        browser = None
        
        try:
            # Create browser instance
            self.logger.info(f"Creating browser instance for {username}")
            browser = self._create_browser_instance()
            
            # First try using stored cookies
            self.logger.info(f"Attempting to create session with cookies for {username}")
            
            # A flag to track if we need manual intervention
            manual_login_needed = False
            
            try:
                # Check if cookies exist and create a session
                has_cookies = browser._check_cookies_exist(username)
                
                if has_cookies:
                    self.logger.info(f"Found cookies for {username}, creating cookie-based session")
                    driver = browser._create_driver(username=username)
                    
                    # Load Instagram profile page
                    driver.get(profile_url)
                    time.sleep(3)
                    
                    # Check if session is valid
                    if "login" in driver.current_url:
                        self.logger.info(f"Cookie session failed for {username}, manual login required")
                        manual_login_needed = True
                    else:
                        self.logger.info(f"Successfully created cookie-based session for {username}")
                else:
                    self.logger.info(f"No cookies found for {username}, manual login required")
                    manual_login_needed = True
            except Exception as e:
                self.logger.error(f"Error with cookie session for {username}: {str(e)}")
                manual_login_needed = True
                
            # If cookies failed or don't exist, initiate manual login
            if manual_login_needed:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = None
                
                self.logger.info(f"Starting manual login for {username}")
                
                # Inform the user they need to manually log in
                print(f"⚠️ Manual login required for account {username}")
                print("Please login to the Instagram account when the browser opens")
                
                # Start manual login process
                manual_login_success = browser.initiate_manual_login(username)
                
                if not manual_login_success:
                    raise Exception(f"Manual login failed or abandoned for {username}")
                
                # Create a new session after manual login
                driver = browser._create_driver(username=username)
                driver.get(profile_url)
                time.sleep(3)
            
            if not driver:
                raise Exception(f"Failed to create valid session for {username}")
            
            self.logger.info(f"Successfully established session for {username}")
            
            # Find and click the follow button
            success = self._perform_follow_action(driver, profile_url)
            
            if success:
                self.logger.info(f"Successfully followed profile using {username}")
                
                # Use Flask app context for database operations
                try:
                    from app import create_app
                    app = create_app()
                    with app.app_context():
                        # Update account last used time
                        self.account_service.update_last_used(username)
                        
                        # Update account action count directly
                        from app.models import InstagramAccount
                        account = InstagramAccount.query.filter_by(username=username).first()
                        if account:
                            account.action_count = account.action_count + 1 if account.action_count else 1
                            from app import db
                            db.session.commit()
                except Exception as e:
                    self.logger.error(f"Error updating account stats: {str(e)}")
                
                progress_queue.put(1)
                result['success'] = True
            else:
                self.logger.warning(f"Failed to follow profile using {username}")
                result['error'] = "Could not find or click follow button"
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                time.sleep(1)  # Give time for driver to close properly
            
        return result

    def _perform_follow_action(self, driver, profile_url):
        """Find and click the follow button on a profile page
        
        Args:
            driver: WebDriver instance
            profile_url: URL of the profile being followed
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure we're on the profile page
            current_url = driver.current_url
            if profile_url not in current_url and not current_url.endswith(profile_url.split('/')[-1]):
                driver.get(profile_url)
                time.sleep(3)
            
            # Check if we're already following
            already_following_selectors = [
                "//button[contains(text(), 'Following')]",
                "//button[contains(text(), 'Requested')]",
                "//div[contains(text(), 'Following')]",
                "//div[contains(text(), 'Requested')]",
                "//span[contains(text(), 'Following')]",
                "//span[contains(text(), 'Requested')]",
                "//div[@dir='auto' and contains(text(), 'Following')]",
                "//div[@dir='auto' and contains(text(), 'Requested')]"
            ]
            
            for selector in already_following_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements and elements[0].is_displayed():
                        self.logger.info("Already following this profile")
                        return True
                except:
                    continue
            
            # Log the page HTML for debugging
            self.logger.info(f"Looking for follow button")
            
            # Find follow button using multiple selectors
            follow_button = None
            
            # Try the exact div structure you provided
            try:
                # Using complex CSS selectors to match the structure
                exact_css_selectors = [
                    "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh div._ap3a._aaco._aacw._aad6._aade",
                    "div._ap3a._aaco._aacw._aad6._aade[dir='auto']",
                    "div.x9f619 div[dir='auto']",
                    "div.x6s0dn4 div[dir='auto']"
                ]
                
                for selector in exact_css_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and "Follow" in element.text and "Following" not in element.text:
                            # Get the parent container that's clickable
                            follow_button = element
                            # Try to get parent elements that might be clickable
                            for _ in range(3):  # Go up to 3 levels up
                                try:
                                    follow_button = follow_button.find_element(By.XPATH, "..")
                                except:
                                    break
                            break
                    if follow_button:
                        break
            except Exception as e:
                self.logger.debug(f"Error finding button with exact structure: {str(e)}")
            
            # If exact structure didn't work, try more general selectors
            if not follow_button:
                follow_selectors = [
                    "//div[contains(text(), 'Follow') and not(contains(text(), 'Following'))]",
                    "//button[contains(text(), 'Follow') and not(contains(text(), 'Following'))]",
                    "//div[@role='button']/div[contains(text(), 'Follow')]",
                    "//span[contains(text(), 'Follow') and not(contains(text(), 'Following'))]",
                    "//div[@dir='auto' and contains(text(), 'Follow') and not(contains(text(), 'Following'))]"
                ]
                
                for selector in follow_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and "Follow" in element.text and "Following" not in element.text:
                                # Try to find a clickable parent
                                follow_button = element
                                for _ in range(3):  # Go up to 3 levels
                                    try:
                                        parent = follow_button.find_element(By.XPATH, "..")
                                        follow_button = parent
                                    except:
                                        break
                                break
                        if follow_button:
                            break
                    except:
                        continue
            
            # Last resort - try to find any element with the text "Follow"
            if not follow_button:
                try:
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Follow')]")
                    for element in elements:
                        if element.is_displayed() and "Follow" == element.text.strip():
                            follow_button = element
                            # Try to get a parent element
                            for _ in range(3):
                                try:
                                    parent = follow_button.find_element(By.XPATH, "..")
                                    follow_button = parent
                                except:
                                    break
                            break
                except:
                    pass
            
            if not follow_button:
                # Try using JavaScript to find and click the follow button
                js_result = driver.execute_script("""
                    // Find all elements that might contain the follow button
                    const possibleElements = [
                        ...document.querySelectorAll('div[dir="auto"]'),
                        ...document.querySelectorAll('button'),
                        ...document.querySelectorAll('div[role="button"]')
                    ];
                    
                    // Look for elements with "Follow" text
                    for (const element of possibleElements) {
                        if (element.textContent === 'Follow') {
                            // Click the element or its parent
                            const clickTarget = element.closest('[role="button"]') || 
                                            element.closest('button') || 
                                            element.closest('div.x9f619') ||
                                            element;
                            clickTarget.click();
                            return true;
                        }
                    }
                    return false;
                """)
                
                if js_result:
                    self.logger.info("Follow button clicked via JavaScript")
                    
                    # Wait longer to confirm follow action
                    time.sleep(5)
                    
                    # Check if the follow button changed in any way
                    try:
                        # Take a screenshot for debugging
                        screenshot_path = f"follow_debug_{int(time.time())}.png"
                        driver.save_screenshot(screenshot_path)
                        self.logger.info(f"Saved screenshot to {screenshot_path}")
                        
                        # Since Instagram doesn't consistently update the UI after following,
                        # we'll assume success if we got this far and we were able to click
                        self.logger.info("Follow action likely successful - continuing with task")
                        return True
                        
                    except Exception as e:
                        self.logger.error(f"Error during follow verification: {str(e)}")
                        # Still return True since the follow action probably worked
                        return True
                
                self.logger.warning("Could not find follow button")
                return False
            
            # Scroll to the button and click with retries
            driver.execute_script("arguments[0].scrollIntoView();", follow_button)
            time.sleep(1)
            
            # Try different click methods
            click_successful = False
            for _ in range(3):  # Try up to 3 times
                try:
                    # Method 1: Regular click
                    follow_button.click()
                    click_successful = True
                    break
                except:
                    try:
                        # Method 2: JavaScript click
                        driver.execute_script("arguments[0].click();", follow_button)
                        click_successful = True
                        break
                    except:
                        try:
                            # Method 3: ActionChains click
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(driver)
                            actions.move_to_element(follow_button)
                            actions.click()
                            actions.perform()
                            click_successful = True
                            break
                        except:
                            time.sleep(1)  # Wait before retry
            
            if click_successful:
                # Wait longer to confirm follow action
                time.sleep(5)
                
                # Check if the follow button changed in any way
                try:
                    # Take a screenshot for debugging
                    screenshot_path = f"follow_debug_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    self.logger.info(f"Saved screenshot to {screenshot_path}")
                    
                    # Since Instagram doesn't consistently update the UI after following,
                    # we'll assume success if we got this far and we were able to click
                    self.logger.info("Follow action likely successful - continuing with task")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Error during follow verification: {str(e)}")
                    # Still return True since the follow action probably worked
                    return True
            else:
                self.logger.warning("Could not click follow button with any method")
                return False
            
        except Exception as e:
            self.logger.error(f"Error performing follow action: {str(e)}")
            return False

    def follow_profile(self, profile_url, num_accounts=1):
        """Follow a profile with multiple accounts
        
        Args:
            profile_url: URL of the Instagram profile to follow
            num_accounts: Number of accounts to use for following
            
        Returns:
            list: Results for each follow attempt
        """
        try:
            self.logger.info(f"Starting follow operation for {profile_url} with {num_accounts} accounts")
            
            # Get active accounts
            accounts = self.account_service.get_active_accounts()
            accounts = [username for username, _ in accounts]
            
            # Fallback: if no accounts from service, try direct DB query
            if not accounts:
                from app.models import InstagramAccount
                db_accounts = InstagramAccount.query.filter_by(is_active=True).all()
                accounts = [account.username for account in db_accounts]
            
            if not accounts:
                raise Exception("No active accounts found")
            
            # Limit number of accounts to use
            num_accounts = min(num_accounts, len(accounts))
            selected_accounts = accounts[:num_accounts]
            
            self.logger.info(f"Using {num_accounts} accounts to follow {profile_url}")
            
            # Setup progress tracking
            all_results = []
            progress_queue = queue.Queue()
            
            # Process in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_account = {}
                
                # Submit tasks for each account
                for username in selected_accounts:
                    future = executor.submit(
                        self._follow_with_account,
                        profile_url,
                        username,
                        progress_queue
                    )
                    future_to_account[future] = username
                
                # Process results as they complete
                completed = 0
                for future in future_to_account:
                    try:
                        result = future.result()
                        all_results.append(result)
                        
                        # Update progress
                        while not progress_queue.empty():
                            progress_queue.get()
                            completed += 1
                            self.update_progress(completed, num_accounts)
                            
                    except Exception as e:
                        username = future_to_account[future]
                        self.logger.error(f"Error in thread for {username}: {str(e)}")
                        all_results.append({
                            'username': username,
                            'target_profile': profile_url,
                            'success': False,
                            'error': str(e)
                        })
            
            # Calculate success rate
            success_count = len([r for r in all_results if r['success']])
            success_rate = (success_count / num_accounts) * 100 if num_accounts > 0 else 0
            self.logger.info(f"Follow operation completed. Success rate: {success_rate:.2f}%")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Follow operation failed: {str(e)}")
            raise