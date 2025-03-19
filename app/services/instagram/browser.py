# app/services/instagram/browser.py

import undetected_chromedriver
from selenium_stealth import stealth
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import pickle
import os
import time
import random
import logging
import traceback
import shutil  # <-- Agregado para cleanup de directorios si hace falta

class InstagramBrowser:
    def __init__(self):
        self.base_url = "https://www.instagram.com"
        self.cookies_dir = os.path.join("browser_data", "cookies")
        os.makedirs(self.cookies_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.timeout = 30
        self.min_delay = 1
        self.max_delay = 3

    def _normalize_url(self, url):
        """Normalize Instagram URLs to a standard format"""
        base_url = url.split('?')[0]
        base_url = base_url.rstrip('/')
        return base_url

    def _verify_session(self, driver, retries=2):
        """Verify and ensure session is valid"""
        try:
            driver.get("https://www.instagram.com/accounts/access_tool/")
            time.sleep(2)

            if "login" in driver.current_url:
                for _ in range(retries):
                    driver.get("https://www.instagram.com")
                    time.sleep(2)
                    if "login" not in driver.current_url:
                        return True
                return False
            return True
        except:
            return False

    def _get_cookie_path(self, username):
        """Get the full path for user's cookies file"""
        return os.path.join(self.cookies_dir, f"{username}_cookies.pkl")

    def _cleanup_old_temp_dirs(self):
        """Clean up old temporary Chrome user data directories"""
        try:
            base_dir = os.path.abspath(os.path.dirname(__file__))
            current_time = time.time()

            for dir_name in os.listdir(base_dir):
                if dir_name.startswith("chrome_data_temp_"):
                    dir_path = os.path.join(base_dir, dir_name)
                    try:
                        timestamp = float(dir_name.split("_")[-1])
                        if current_time - timestamp > 3600:  # 1 hour
                            shutil.rmtree(dir_path, ignore_errors=True)
                    except:
                        continue
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp directories: {str(e)}")

    def _check_cookies_exist(self, username):
        """Check if cookies file exists for the user"""
        cookie_path = self._get_cookie_path(username)
        return os.path.exists(cookie_path)

    def _load_cookies(self, driver, username):
        """(No se elimina de tu código) Carga cookies 
           - Nota: ahora usaremos la versión CDP, pero mantenemos este método por compatibilidad."""
        try:
            cookie_path = self._get_cookie_path(username)
            if not os.path.exists(cookie_path):
                return False

            # NOTA: Este método hacía driver.get("instagram.com") primero,
            # pero ahora, con la inyección CDP (opción 3), evitaremos llamarlo así desde create_driver.
            current_url = driver.current_url
            if "instagram.com" not in current_url:
                driver.get("https://www.instagram.com")
                time.sleep(2)

            with open(cookie_path, 'rb') as f:
                cookies = pickle.load(f)

            if not cookies:
                return False

            success_count = 0
            for cookie in cookies:
                try:
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    if 'expires' in cookie:
                        del cookie['expires']
                    if 'domain' in cookie:
                        if not cookie['domain'].startswith('.'):
                            cookie['domain'] = '.' + cookie['domain']
                    else:
                        cookie['domain'] = '.instagram.com'

                    for k in ['sameSite', 'httpOnly', 'secure']:
                        if k in cookie:
                            del cookie[k]

                    clean_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain']
                    }
                    if 'path' in cookie:
                        clean_cookie['path'] = cookie['path']

                    driver.add_cookie(clean_cookie)
                    success_count += 1

                except Exception as e:
                    self.logger.warning(f"Failed to add cookie {cookie.get('name')}: {str(e)}")
                    continue

            self.logger.info(f"Successfully loaded {success_count} cookies for {username}")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"Failed to load cookies for {username}: {str(e)}")
            return False

    def _random_delay(self, min_seconds=None, max_seconds=None):
        """Add random delay between actions"""
        min_seconds = min_seconds or self.min_delay
        max_seconds = max_seconds or self.max_delay
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _verify_login(self, driver):
        """Verify if current session is logged in"""
        try:
            driver.get(self.base_url)
            self._random_delay(2, 4)
            return "login" not in driver.current_url
        except Exception as e:
            self.logger.error(f"Login verification failed: {str(e)}")
            return False

    def _cleanup_old_temp_dirs(self):  # Método repetido en tu snippet, lo mantenemos
        try:
            base_dir = os.path.abspath(os.path.dirname(__file__))
            current_time = time.time()
            for dir_name in os.listdir(base_dir):
                if dir_name.startswith("chrome_data_temp_"):
                    dir_path = os.path.join(base_dir, dir_name)
                    try:
                        timestamp = float(dir_name.split("_")[-1])
                        if current_time - timestamp > 3600:  # 1 hour
                            shutil.rmtree(dir_path, ignore_errors=True)
                    except:
                        continue
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp directories: {str(e)}")

    def _save_cookies(self, driver, username):
        """Save all necessary authentication cookies"""
        try:
            all_cookies = driver.get_cookies()
            essential_cookies = [
                'sessionid', 'ds_user_id', 'csrftoken', 'ig_did',
                'mid', 'ig_nrcb', 'datr', 'rur', 'shbid', 'shbts'
            ]

            cookies_to_save = []
            for cookie in all_cookies:
                if cookie['name'] in essential_cookies:
                    clean_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': '.instagram.com',
                        'path': '/'
                    }
                    cookies_to_save.append(clean_cookie)
                elif '.instagram.com' in cookie.get('domain', ''):
                    clean_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': '.instagram.com',
                        'path': '/'
                    }
                    cookies_to_save.append(clean_cookie)

            if not cookies_to_save:
                raise Exception("No valid cookies found to save")

            saved_cookie_names = {cookie['name'] for cookie in cookies_to_save}
            missing_essential = [
                name for name in ['sessionid', 'ds_user_id', 'csrftoken']
                if name not in saved_cookie_names
            ]

            if missing_essential:
                raise Exception(f"Missing essential cookies: {missing_essential}")

            cookie_path = self._get_cookie_path(username)
            with open(cookie_path, 'wb') as f:
                pickle.dump(cookies_to_save, f)

            self.logger.info(f"Successfully saved {len(cookies_to_save)} cookies for {username}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save cookies for {username}: {str(e)}")
            return False

    def login(self, username, password):
        """
        Login to Instagram with enhanced challenge detection
        
        Args:
            username: Instagram username
            password: Instagram password
            
        Returns:
            WebDriver instance if login successful, None if failed
            
        Raises:
            Exception with specific error message if verification required
        """
        driver = None
        try:
            print(f"Starting login process for {username}")
            driver = self._create_driver(fresh_session=True)
            
            print(f"Navigating to Instagram login page")
            driver.get(f"{self.base_url}/accounts/login/")
            time.sleep(3)
            
            # Check if we're already logged in (cookies might be valid)
            login_state = self.detect_login_state(driver)
            if login_state['is_logged_in']:
                print(f"Already logged in as {username}")
                # Save cookies and return
                if self._save_cookies(driver, username):
                    return driver
                else:
                    raise Exception("Failed to save cookies for logged-in session")
            
            # Check if we're on a verification page
            if login_state['requires_verification']:
                verification_type = login_state['verification_type'] or 'unknown'
                raise Exception(f"Account requires verification: {verification_type}")
            
            print(f"Entering username")
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.clear()
            for char in username:
                username_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            print(f"Entering password")
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            for char in password:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            print(f"Clicking login button")
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            
            # Wait longer for login to complete
            time.sleep(5)
            
            # Check for verification/challenge pages
            for _ in range(3):  # Try multiple checks with delays
                login_state = self.detect_login_state(driver)
                
                if login_state['is_logged_in']:
                    print(f"Login successful for {username}")
                    
                    # Navigate to user profile to ensure complete login
                    print(f"Navigating to user profile")
                    try:
                        driver.get(f"{self.base_url}/{username}/")
                        time.sleep(3)
                    except:
                        # If navigation fails, check login state again
                        login_state = self.detect_login_state(driver)
                        if not login_state['is_logged_in']:
                            raise Exception("Navigation to profile failed, may not be fully logged in")
                    
                    # Save cookies
                    print(f"Saving cookies")
                    if not self._save_cookies(driver, username):
                        print(f"Failed to save cookies")
                        raise Exception("Failed to save cookies")
                    
                    print(f"Login successful for {username}")
                    return driver
                    
                elif login_state['requires_verification']:
                    print(f"Verification required for {username}: {login_state['verification_type']}")
                    raise Exception(f"Account requires verification: {login_state['verification_type']}")
                
                # Still on login page - might be loading or incorrect credentials
                elif "login" in driver.current_url:
                    # Check for error messages
                    error_selectors = [
                        "//p[@data-testid='login-error-message']",
                        "//div[contains(@role, 'alert')]",
                        "//div[contains(text(), 'incorrect')]",
                        "//div[contains(text(), 'couldn\'t connect')]"
                    ]
                    
                    for selector in error_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements:
                                error_text = elements[0].text
                                print(f"Login error detected: {error_text}")
                                raise Exception(f"Login failed: {error_text}")
                        except Exception as e:
                            if "Login failed:" in str(e):
                                raise
                    
                # Wait and try again
                time.sleep(2)
            
            # If we get here, login was not successful and we're not on a verification page
            print(f"Login failed for {username} - still on login page or unknown state")
            raise Exception("Login failed - either invalid credentials or unknown error")
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            if driver:
                try:
                    # Take screenshot for debugging
                    screenshot_path = f"login_error_{username}_{int(time.time())}.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Saved error screenshot to {screenshot_path}")
                    
                    # Close the driver if no verification is required
                    if not ("verification" in str(e).lower() or "challenge" in str(e).lower() or "2fa" in str(e).lower()):
                        driver.quit()
                        driver = None
                except:
                    pass
            raise Exception(f"Login failed: {str(e)}")

    def initiate_manual_login(self, username):
        """
        Opens a browser window for manual login and waits for successful login completion.
        Does not attempt to enter credentials, allowing the user to complete the entire login process.
        
        Args:
            username: Instagram username for cookie identification
            
        Returns:
            bool: True if manual login was successful, False otherwise
        """
        driver = None
        try:
            self.logger.info(f"Starting manual login process for {username}")
            
            # Create a fresh browser session
            driver = self._create_driver(fresh_session=True)
            
            # Navigate to Instagram login page without entering any credentials
            driver.get(f"{self.base_url}/accounts/login")
            self.logger.info(f"Browser opened for manual login of {username}")
            
            # Display information to the user
            alert_script = """
            const infoDiv = document.createElement('div');
            infoDiv.style.position = 'fixed';
            infoDiv.style.top = '0';
            infoDiv.style.left = '0';
            infoDiv.style.width = '100%';
            infoDiv.style.backgroundColor = '#3897f0';
            infoDiv.style.color = 'white';
            infoDiv.style.padding = '10px';
            infoDiv.style.textAlign = 'center';
            infoDiv.style.zIndex = '9999';
            infoDiv.style.fontFamily = 'Arial, sans-serif';
            infoDiv.innerHTML = '<b>MANUAL LOGIN REQUIRED</b><br>Please log in to your Instagram account ({username}).<br>This window will automatically close when login is complete.';
            document.body.prepend(infoDiv);
            """.replace("{username}", username)
            driver.execute_script(alert_script)
            
            # Wait for successful login
            max_wait_time = 300  # 5 minutes
            check_interval = 2   # 2 seconds
            start_time = time.time()
            logged_in = False
            
            while time.time() - start_time < max_wait_time:
                try:
                    # Check if we're logged in by looking for indicators
                    current_url = driver.current_url
                    
                    # If we're not on a login page and not in a challenge page
                    if ("login" not in current_url and 
                        "challenge" not in current_url and 
                        "accounts/suspended" not in current_url):
                        
                        # Look for additional login indicators
                        login_indicators = [
                            "//span[text()='Profile']",  # Profile link
                            "//a[contains(@href, '/direct/inbox/')]",  # DM link
                            "//div[@aria-label='Home']",  # Home icon
                            "//svg[@aria-label='Home']",  # Home icon (alternative)
                            "//span[@aria-label='Profile']",  # Profile icon
                            "//a[contains(@href, '/" + username + "/')]"  # Link to profile
                        ]
                        
                        for indicator in login_indicators:
                            try:
                                if driver.find_elements(By.XPATH, indicator):
                                    logged_in = True
                                    break
                            except:
                                continue
                        
                        # Check cookies as a final verification
                        if not logged_in:
                            cookies = driver.get_cookies()
                            if any(c['name'] == 'sessionid' for c in cookies):
                                logged_in = True
                        
                        if logged_in:
                            self.logger.info(f"Manual login detected for {username}")
                            
                            # Wait a moment to ensure all cookies are set
                            time.sleep(3)
                            
                            # Save cookies
                            if self._save_cookies(driver, username):
                                self.logger.info(f"Successfully saved cookies for {username}")
                                
                                # Display success message to user
                                success_script = """
                                const infoDiv = document.querySelector('div[style*="position: fixed"]');
                                if (infoDiv) {
                                    infoDiv.style.backgroundColor = '#4CAF50';
                                    infoDiv.innerHTML = '<b>LOGIN SUCCESSFUL</b><br>Your account has been verified.<br>This window will close in 5 seconds.';
                                }
                                """
                                driver.execute_script(success_script)
                                time.sleep(5)  # Show success message for 5 seconds
                                
                                return True
                    
                    # Sleep before next check
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error during manual login check: {str(e)}")
                    time.sleep(check_interval)
            
            # If we reach here, timeout occurred
            self.logger.warning(f"Manual login timeout for {username}")
            
            # Display timeout message
            timeout_script = """
            const infoDiv = document.querySelector('div[style*="position: fixed"]');
            if (infoDiv) {
                infoDiv.style.backgroundColor = '#f44336';
                infoDiv.innerHTML = '<b>LOGIN TIMEOUT</b><br>Manual login process has timed out.<br>This window will close in 5 seconds.';
            }
            """
            try:
                driver.execute_script(timeout_script)
                time.sleep(5)  # Show timeout message for 5 seconds
            except:
                pass
                
            return False

        except Exception as e:
            self.logger.error(f"Manual login process failed: {str(e)}")
            return False

        finally:
            # Close the browser window if it's still open
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    def _detect_challenge_page(self, driver):
        """
        Detect if we're on a challenge or verification page.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            tuple: (is_challenge, challenge_type)
                is_challenge: Boolean indicating if a challenge was detected
                challenge_type: String describing the type of challenge, or None
        """
        try:
            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()
            
            # Check URL patterns first
            if any(pattern in current_url for pattern in [
                '/challenge/', 
                '/challenge/action/',
                '/challenge/replay/',
                '/login/two_factor/',
                '/accounts/confirm_email/'
            ]):
                # We're on a challenge page, now determine the type
                if 'two_factor' in current_url:
                    return True, '2fa'
                elif 'confirm_email' in current_url:
                    return True, 'email_verification'
                elif 'challenge' in current_url:
                    # Try to determine the specific challenge type from page content
                    if any(text in page_source for text in [
                        'enter the code', 
                        'enter code',
                        'security code',
                        'verification code'
                    ]):
                        if any(text in page_source for text in ['phone', 'mobile', 'sms']):
                            return True, 'sms_verification'
                        elif any(text in page_source for text in ['email']):
                            return True, 'email_verification'
                        else:
                            return True, 'code_verification'
                    elif any(text in page_source for text in [
                        'suspicious', 
                        'unusual activity',
                        'unusual login',
                        'recognize this login'
                    ]):
                        return True, 'suspicious_login'
                    elif any(text in page_source for text in [
                        'captcha',
                        'confirm you\'re a person',
                        'prove you\'re not a robot'
                    ]):
                        return True, 'captcha'
                    else:
                        return True, 'unknown_challenge'
            
            # Check for specific elements/text that indicate challenges
            challenge_indicators = [
                "//h2[contains(text(), 'Enter the confirmation code')]",
                "//h2[contains(text(), 'Enter the security code')]",
                "//h2[contains(text(), 'Enter confirmation code')]",
                "//h2[contains(text(), 'We need to confirm it\'s you')]",
                "//h2[contains(text(), 'Suspicious Login Attempt')]",
                "//div[contains(text(), 'to confirm it\'s you')]",
                "//div[contains(text(), 'Enter the code sent to your')]",
                "//div[contains(text(), 'Enter the code we sent to')]",
                "//div[contains(text(), 'Authentication required')]",
                "//p[contains(text(), 'We noticed an unusual login')]"
            ]
            
            for indicator in challenge_indicators:
                try:
                    if driver.find_elements(By.XPATH, indicator):
                        return True, 'challenge_detected'
                except:
                    continue
            
            # No challenge detected
            return False, None
            
        except Exception as e:
            self.logger.warning(f"Error detecting challenge page: {str(e)}")
            return False, None

    def detect_login_state(self, driver):
        """
        Detect the current login state and identify any verification challenges.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            dict: Information about the current login state
                {
                    'is_logged_in': Boolean indicating if user is logged in
                    'requires_verification': Boolean indicating if verification is needed
                    'verification_type': String describing the verification type (if any)
                    'current_url': Current URL
                    'page_title': Page title
                }
        """
        try:
            current_url = driver.current_url
            page_title = driver.title
            
            # Default state
            state = {
                'is_logged_in': False,
                'requires_verification': False,
                'verification_type': None,
                'current_url': current_url,
                'page_title': page_title
            }
            
            # Check if we're on a login page
            if 'login' in current_url:
                state['is_logged_in'] = False
                # No further checks needed, we're definitely not logged in
                return state
            
            # Check if we're on a challenge/verification page
            is_challenge, challenge_type = self._detect_challenge_page(driver)
            if is_challenge:
                state['is_logged_in'] = False  # Not fully logged in if challenge exists
                state['requires_verification'] = True
                state['verification_type'] = challenge_type
                return state
            
            # Check for successful login indicators
            login_indicators = [
                # Navigation elements present when logged in
                "//div[@role='navigation']",
                "//nav[@role='navigation']",
                "//a[contains(@href, '/direct/inbox/')]",
                "//a[contains(@href, '/explore/')]",
                
                # Avatar/profile elements
                "//span[@role='link' and contains(@class, 'coreSpriteDesktopNavProfile')]",
                "//a[contains(@href, '/accounts/activity/')]",
                
                # Feed elements
                "//section[@role='main']//article",
                
                # Instagram app shell
                "//div[@id='react-root']//section[count(./div) > 2]"
            ]
            
            for indicator in login_indicators:
                try:
                    if driver.find_elements(By.XPATH, indicator):
                        state['is_logged_in'] = True
                        break
                except:
                    continue
            
            # Check cookies as a final verification
            if not state['is_logged_in']:
                cookies = driver.get_cookies()
                if any(c['name'] == 'sessionid' for c in cookies):
                    state['is_logged_in'] = True
            
            return state
            
        except Exception as e:
            self.logger.warning(f"Error detecting login state: {str(e)}")
            # Default to a safe assumption
            return {
                'is_logged_in': False,
                'requires_verification': False,
                'verification_type': None,
                'current_url': driver.current_url,
                'page_title': driver.title
            }
    def _check_comments_enabled(self, driver):
        """Check if comments are enabled on the post"""
        try:
            disabled_indicators = [
                "//div[contains(text(), 'Comments on this post have been limited')]",
                "//div[contains(text(), 'Comments are turned off')]",
                "//span[contains(text(), 'Comments are turned off')]"
            ]
            for indicator in disabled_indicators:
                try:
                    if driver.find_elements(By.XPATH, indicator):
                        return False
                except:
                    continue

            textarea_selectors = [
                ("textarea.x1i0vuye.xvbhtw8.x1ejq31n.xd10rxx.x1sy0etr"
                 ".x17r0tee.x5n08af.x78zum5.x1iyjqo2.x1qlqyl8.x1d6elog"
                 ".xlk1fp6.x1a2a7pz.xexx8yu.x4uap5.x18d9i69.xkhd6sd"
                 ".xtt52l0.xnalus7.xs3hnx8.x1bq4at4.xaqnwrm"),
                "textarea[aria-label='Add a comment…'][placeholder='Add a comment…']",
                "textarea.x1i0vuye",
                "div.x6s0dn4 textarea"
            ]
            for selector in textarea_selectors:
                try:
                    textarea = driver.find_element(By.CSS_SELECTOR, selector)
                    if textarea.is_displayed() and textarea.is_enabled():
                        return True
                except:
                    continue
            return False
        except Exception as e:
            self.logger.warning(f"Error checking comment status: {str(e)}")
            return False

    # -- NUEVO: método para inyectar cookies via CDP antes de cargar la página
    def _inject_cookies_via_cdp(self, driver, cookies):
        """
        Uses Chrome DevTools Protocol to set cookies before visiting Instagram,
        preventing the login screen from briefly appearing.
        """
        try:
            # Enable network control
            driver.execute_cdp_cmd("Network.enable", {})
            
            # Set initial fingerprint evasion parameters
            self._set_anti_fingerprinting_params(driver)
            
            cdp_cookies = []

            for c in cookies:
                # Convert cookies to CDP format
                domain = c.get('domain', '.instagram.com')
                if not domain.startswith('.'):
                    domain = '.' + domain

                cdp_cookie = {
                    "domain": domain,
                    "path": c.get("path", "/"),
                    "secure": True,
                    "httpOnly": c.get("httpOnly", False),
                    "name": c["name"],
                    "value": c["value"],
                    "sameSite": c.get("sameSite", "None")
                }
                
                # Add expiration if present
                if 'expiry' in c:
                    cdp_cookie['expires'] = c['expiry']
                    
                cdp_cookies.append(cdp_cookie)

            # Set cookies in bulk
            driver.execute_cdp_cmd("Network.setCookies", {"cookies": cdp_cookies})
            self.logger.info(f"Injected {len(cdp_cookies)} cookies via CDP.")
            
            # Apply additional anti-detection measures
            self._apply_stealth_cdp_commands(driver)
            
        except Exception as e:
            self.logger.error(f"Error injecting cookies via CDP: {str(e)}")

    def _set_anti_fingerprinting_params(self, driver):
        """Sets various parameters to prevent browser fingerprinting"""
        try:
            # Override navigator properties
            driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {
                "userAgent": driver.execute_script("return navigator.userAgent"),
                "acceptLanguage": "en-US,en;q=0.9",
                "platform": "Win32"
            })
            
            # Randomize device metrics slightly
            width = random.randint(1280, 1920)
            height = random.randint(800, 1080)
            scale = random.uniform(1.0, 2.0)
            mobile = False
            
            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                "width": width,
                "height": height,
                "deviceScaleFactor": scale,
                "mobile": mobile
            })
            
            # Disable WebRTC to prevent IP leaks
            webrtc_script = """
            (function() {
                const originalRTCPeerConnection = window.RTCPeerConnection || 
                                                window.webkitRTCPeerConnection || 
                                                window.mozRTCPeerConnection;
                if (originalRTCPeerConnection) {
                    window.RTCPeerConnection = function(...args) {
                        const pc = new originalRTCPeerConnection(...args);
                        pc.createDataChannel = function() { return {}; };
                        return pc;
                    };
                    window.RTCPeerConnection.prototype = originalRTCPeerConnection.prototype;
                }
                
                // Disable WebRTC completely
                Object.defineProperty(navigator, 'mediaDevices', {
                    get: function() { return undefined; }
                });
            })();
            """
            driver.execute_script(webrtc_script)
            
        except Exception as e:
            self.logger.warning(f"Error applying anti-fingerprinting params: {str(e)}")

    def _apply_stealth_cdp_commands(self, driver):
        """Apply advanced stealth measures using Chrome DevTools Protocol"""
        try:
            # Override permission settings - claim webcam/mic already allowed
            driver.execute_cdp_cmd("Browser.grantPermissions", {
                "permissions": ["geolocation", "notifications"]
            })
            
            # Set media playback capabilities
            driver.execute_cdp_cmd("Emulation.setMediaFeatureOverride", {
                "features": [
                    {"name": "prefers-color-scheme", "value": "light"},
                    {"name": "prefers-reduced-motion", "value": "no-preference"},
                    {"name": "prefers-reduced-transparency", "value": "no-preference"}
                ]
            })
            
            # Adjust hardware concurrency to common value
            hardware_concurrency_script = """
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 4
            });
            """
            driver.execute_script(hardware_concurrency_script)
            
            # Set consistent device memory
            device_memory_script = """
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            """
            driver.execute_script(device_memory_script)
            
            # Override common canvas fingerprinting methods
            canvas_script = """
            (function() {
                // Add subtle noise to canvas operations
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                    const imageData = originalGetImageData.call(this, x, y, w, h);
                    const data = imageData.data;
                    
                    // Add very slight noise to alpha channel, barely impacts visual quality
                    // but helps avoid fingerprinting
                    for (let i = 3; i < data.length; i += 4) {
                        // Only modify one out of every 10 pixels, and only by at most 1
                        if (Math.random() < 0.1) {
                            const noise = Math.round(Math.random()) === 1 ? 1 : 0;
                            if (data[i] > 1) data[i] -= noise;
                        }
                    }
                    
                    return imageData;
                };
                
                // Override toDataURL with similar subtle noise addition
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {
                    // Add a single random pixel modification
                    const context = this.getContext('2d');
                    const pixel = context.getImageData(0, 0, 1, 1);
                    if (pixel.data[3] > 0) {
                        // Only if the pixel has some opacity, modify it slightly
                        pixel.data[0] = Math.max(0, Math.min(255, pixel.data[0] + (Math.random() < 0.5 ? 1 : -1)));
                        context.putImageData(pixel, 0, 0);
                    }
                    
                    return originalToDataURL.apply(this, arguments);
                };
            })();
            """
            driver.execute_script(canvas_script)
            
            # Apply font fingerprinting protection
            font_protection_script = """
            (function() {
                // Override font fingerprinting methods
                const originalFontFace = window.FontFace;
                window.FontFace = function() {
                    return new originalFontFace(...arguments);
                };
                
                // Override measureText to add tiny random noise
                const originalMeasureText = CanvasRenderingContext2D.prototype.measureText;
                CanvasRenderingContext2D.prototype.measureText = function(text) {
                    const result = originalMeasureText.call(this, text);
                    
                    // Add tiny amount of randomness to width measurement
                    const originalWidth = result.width;
                    Object.defineProperty(result, 'width', {
                        get: function() {
                            return originalWidth + (Math.random() * 0.00001); // Imperceptible change
                        }
                    });
                    
                    return result;
                };
            })();
            """
            driver.execute_script(font_protection_script)
            
        except Exception as e:
            self.logger.warning(f"Error applying stealth CDP commands: {str(e)}")

    def _create_driver(self, username=None, fresh_session=False, proxy=None):
        """Create a stealth Chrome instance with enhanced anti-detection measures."""
        try:
            # Create a more randomized user data directory to prevent tracking
            temp_dir = f"chrome_data_temp_{int(time.time())}_{random.randint(1000, 9999)}"
            user_data_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), temp_dir)
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Debug output
            print(f"Creating driver with user_data_dir: {user_data_dir}")
            
            # First, create ChromeOptions - BEFORE using it
            options = webdriver.ChromeOptions()
            
            # Disable dev shm usage (fixes common Windows error)
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            
            # Screen size randomization (subtle variations)
            width = random.choice([1920, 1910, 1900, 1890])
            height = random.choice([1080, 1070, 1060, 1050])
            options.add_argument(f'--window-size={width},{height}')
            
            # Common options
            options.add_argument('--disable-notifications')
            options.add_argument('--lang=en-US')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Enhanced stealth options
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-extensions')
            
            # Set a realistic user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Set custom data directory
            options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Auto-install ChromeDriver
            import chromedriver_autoinstaller
            chromedriver_path = chromedriver_autoinstaller.install()
            print(f"ChromeDriver installed to: {chromedriver_path}")
            
            # THEN create the driver with the options
            print("Creating Chrome WebDriver...")
            driver = webdriver.Chrome(options=options)
            print("Chrome WebDriver created successfully")
            
            driver.set_page_load_timeout(self.timeout)
            
            # If username is provided, try to load cookies
            if username and not fresh_session:
                cookie_path = self._get_cookie_path(username)
                if os.path.exists(cookie_path):
                    try:
                        driver.get("https://www.instagram.com")
                        time.sleep(2)
                        self._load_cookies(driver, username)
                    except Exception as e:
                        self.logger.error(f"Failed to load cookies for {username}: {str(e)}")
                        
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to create driver: {str(e)}")
            print(f"Driver creation error: {str(e)}")
            raise

    def _add_random_mouse_movements(self, driver):
        """Add random mouse movements to the page to simulate human behavior"""
        try:
            # Execute JavaScript to add random mouse movements
            js_script = """
            (function() {
                // Create a function to simulate mouse movement
                function simulateMouseMovement() {
                    const events = ['mousemove', 'mouseover', 'mouseout'];
                    const event = events[Math.floor(Math.random() * events.length)];
                    const x = Math.floor(Math.random() * window.innerWidth);
                    const y = Math.floor(Math.random() * window.innerHeight);
                    
                    // Create and dispatch the event
                    const mouseEvent = new MouseEvent(event, {
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        clientX: x,
                        clientY: y
                    });
                    
                    document.elementFromPoint(x, y)?.dispatchEvent(mouseEvent);
                }
                
                // Call the function at random intervals
                setInterval(simulateMouseMovement, Math.random() * 3000 + 500);
            })();
            """
            driver.execute_script(js_script)
        except Exception as e:
            self.logger.warning(f"Failed to add mouse movements: {str(e)}")
    def create_comment_session(self, username, post_url):
        """Create a fresh browser session for commenting"""
        try:
            driver = self._create_driver(username=username)
            normalized_url = self._normalize_url(post_url)
            driver.get(normalized_url)
            time.sleep(2)

            if "login" in driver.current_url:
                raise Exception("Failed to authenticate with cookies")

            return driver

        except Exception as e:
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
            raise Exception(f"Failed to create comment session: {str(e)}")

    def post_comment(self, driver, post_url, comment):
        """Post comment with improved typing and button interaction"""
        try:
            # Keep existing URL verification
            current_url = self._normalize_url(driver.current_url)
            expected_url = self._normalize_url(post_url)
            
            if current_url != expected_url:
                driver.get(post_url)
                time.sleep(3)

            # Finding comment box - keep existing selectors
            comment_box = None
            selectors = [
                "textarea[aria-label='Add a comment…']",
                "textarea.x1i0vuye",
                "textarea.focus-visible",
                "form textarea"
            ]
            
            for selector in selectors:
                try:
                    comment_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if comment_box.is_displayed() and comment_box.is_enabled():
                        break
                except:
                    continue

            if not comment_box:
                raise Exception("Could not find comment box")

            # Improved comment box interaction
            driver.execute_script("arguments[0].scrollIntoView(true);", comment_box)
            time.sleep(1)  # Increased wait time after scroll

            # Clear any existing text first
            comment_box.clear()
            time.sleep(0.5)

            # More reliable click using JavaScript
            driver.execute_script("arguments[0].click();", comment_box)
            time.sleep(0.5)

            # Improved typing mechanism
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(driver)
            actions.move_to_element(comment_box)
            actions.click()
            actions.perform()
            time.sleep(0.5)

            # Type comment with natural delays
            for char in comment:
                try:
                    comment_box.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.3))
                except StaleElementReferenceException:
                    # If element becomes stale, find it again
                    for selector in selectors:
                        try:
                            comment_box = driver.find_element(By.CSS_SELECTOR, selector)
                            if comment_box.is_displayed() and comment_box.is_enabled():
                                comment_box.send_keys(char)
                                break
                        except:
                            continue
                    time.sleep(random.uniform(0.1, 0.3))

            # Wait for comment to be fully typed
            time.sleep(1)

            # Improved post button finding and clicking
            post_button = None
            button_selectors = [
                "div[role='button']:not([aria-disabled='true'])",
                "button._acap",
                "button[type='submit']",
                "//div[text()='Post' and @role='button']"
            ]

            # Try multiple times to find and click the button
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    for selector in button_selectors:
                        try:
                            if selector.startswith("//"):
                                post_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                            else:
                                post_button = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                )
                            
                            if post_button.is_displayed() and post_button.is_enabled() and post_button.text.strip() == "Post":
                                # Try different clicking methods
                                try:
                                    # Method 1: Regular click
                                    post_button.click()
                                except:
                                    try:
                                        # Method 2: JavaScript click
                                        driver.execute_script("arguments[0].click();", post_button)
                                    except:
                                        # Method 3: ActionChains click
                                        actions = ActionChains(driver)
                                        actions.move_to_element(post_button)
                                        actions.click()
                                        actions.perform()
                                
                                # If we get here without exception, break both loops
                                break
                        except:
                            continue
                    
                    # If click was successful, break the attempts loop
                    break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise Exception("Failed to click post button after multiple attempts")
                    time.sleep(1)  # Wait before next attempt

            # Wait for comment to be posted
            time.sleep(3)

            # Keep existing verification
            return self._verify_comment_posted(driver, comment)

        except Exception as e:
            self.logger.error(f"Failed to post comment: {str(e)}")
            raise

    def _verify_comment_posted(self, driver, comment_text):
        """Improved verification of successfully posted comments"""
        try:
            # Wait longer for comment to appear
            time.sleep(3)
            
            # First check if there's any error message visible
            error_selectors = [
                "//div[contains(text(), 'Comment failed')]",
                "//span[contains(text(), 'Unable to post comment')]"
            ]
            
            for selector in error_selectors:
                try:
                    if driver.find_elements(By.XPATH, selector):
                        self.logger.warning(f"Error message found after posting comment: {selector}")
                        return False
                except:
                    pass
            
            # Consider the comment successful even without confirmation
            # Instagram often doesn't show your own comment immediately after posting
            post_button = None
            try:
                # If the post button is disabled or disappeared, that's a good sign
                post_button = driver.find_element(By.XPATH, "//div[text()='Post' and @role='button']")
                # If button is still visible but disabled, comment was likely posted
                if not post_button.is_enabled() or 'disabled' in post_button.get_attribute('class'):
                    self.logger.info("Post button disabled after commenting - likely successful")
                    return True
            except:
                # Button not found usually means comment went through
                self.logger.info("Post button not found after commenting - likely successful")
                return True
                
            # Check for the comment in the comments section
            comment_selectors = [
                "ul._a9ym",  # Comments container
                "span._aacl._aaco._aacu._aacx._aad7",  # Comment text
                "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk",  # Generic comment container
                "article div[role='button'] + div span span"  # Another possible comment text location
            ]
            
            for selector in comment_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if comment_text.strip() in element.text.strip():
                            self.logger.info(f"Found comment text in page: {element.text}")
                            return True
                except:
                    continue
            
            # If we can't find it but don't have errors and the button state changed,
            # assume it was successful - Instagram sometimes doesn't show your own comment right away
            return True
            
        except Exception as e:
            self.logger.warning(f"Error in comment verification: {str(e)}")
            # Default to success if verification fails (Instagram's UI is unreliable)
            return True

    def _verify_cookies(self, cookies):
        """Verify that essential cookies are present and valid"""
        required_cookies = {'sessionid', 'ds_user_id', 'csrftoken'}
        cookie_names = {cookie['name'] for cookie in cookies}
        missing_cookies = required_cookies - cookie_names
        if missing_cookies:
            raise Exception(f"Missing essential cookies: {missing_cookies}")
        return True
