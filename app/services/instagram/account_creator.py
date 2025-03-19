# app/services/instagram/account_creator.py

import os
import time
import random
import logging
import string
import tempfile
from PIL import Image
import io
import requests
import re
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from ..instagram.browser import InstagramBrowser
from ...utils.proxy_manager import ProxyManager
from ...utils.email_verifier import EmailVerifier
from ...utils.captcha_solver import CaptchaSolver
class InstagramBotDetectionCountermeasures:
    """Helper class with Instagram-specific anti-detection measures"""
    
    @staticmethod
    def apply_to_driver(driver, logger):
        """Apply all countermeasures to the given driver"""
        try:
            # Apply all countermeasures
            InstagramBotDetectionCountermeasures._apply_viewport_emulation(driver)
            InstagramBotDetectionCountermeasures._disable_automation_flags(driver)
            InstagramBotDetectionCountermeasures._emulate_human_behavior(driver)
            InstagramBotDetectionCountermeasures._modify_navigator_properties(driver)
            InstagramBotDetectionCountermeasures._inject_visual_features(driver)
            logger.info("Applied Instagram-specific bot detection countermeasures")
            return True
        except Exception as e:
            logger.error(f"Failed to apply bot detection countermeasures: {str(e)}")
            return False
    
    @staticmethod
    def _apply_viewport_emulation(driver):
        """Apply viewport emulation to match common device sizes"""
        # Pick a random common viewport size
        common_viewports = [
            {"width": 1366, "height": 768},  # Most common laptop
            {"width": 1920, "height": 1080},  # FHD desktop
            {"width": 1440, "height": 900},   # MacBook
            {"width": 1536, "height": 864},   # Common Windows laptop
            {"width": 1280, "height": 720}    # HD laptop
        ]
        
        viewport = random.choice(common_viewports)
        width, height = viewport["width"], viewport["height"]
        
        # Add slight randomization
        width += random.randint(-5, 5)
        height += random.randint(-5, 5)
        
        # Set viewport size
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": width,
            "height": height,
            "deviceScaleFactor": random.uniform(1.0, 2.0),
            "mobile": False
        })
        
        # Set window size to match
        driver.set_window_size(width, height)
    
    @staticmethod
    def _disable_automation_flags(driver):
        """Disable automation flags that Instagram may check"""
        scripts = [
            # Disable navigator.webdriver flag
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """,
            
            # Clear automation-related attributes
            """
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """,
            
            # Hide chromedriver reference
            """
            const oldQuery = window.document.querySelector;
            window.document.querySelector = function(selector) {
                if (selector.includes('chromium') || selector.includes('driver')) {
                    return null;
                }
                return oldQuery.apply(this, arguments);
            };
            """
        ]
        
        for script in scripts:
            try:
                driver.execute_script(script)
            except:
                pass
    
    @staticmethod
    def _emulate_human_behavior(driver):
        """Add scripts to emulate human-like behavior"""
        human_scripts = [
            # Add human scrolling behavior
            """
            (function() {
                // Add random scrolling behavior
                function randomScroll() {
                    if (Math.random() < 0.7) { // 70% chance to perform a scroll
                        const scrollAmount = Math.floor(Math.random() * 100);
                        window.scrollBy(0, scrollAmount);
                        
                        // Sometimes scroll back up
                        if (Math.random() < 0.3) {
                            setTimeout(() => {
                                window.scrollBy(0, -Math.floor(Math.random() * 50));
                            }, Math.random() * 1000 + 500);
                        }
                    }
                }
                
                // Add mouse movement to elements on hover
                document.addEventListener('mouseover', function(e) {
                    if (Math.random() < 0.3 && e.target.tagName !== 'BODY') {
                        setTimeout(() => {
                            randomScroll();
                        }, Math.random() * 500);
                    }
                });
                
                // Occasionally perform random scrolls
                setInterval(randomScroll, Math.random() * 5000 + 2000);
            })();
            """,
            
            # Add small delays to keyboard input to mimic typing
            """
            (function() {
                // Override addEventListener to add random delays to keyboard events
                const originalAddEventListener = EventTarget.prototype.addEventListener;
                EventTarget.prototype.addEventListener = function(type, listener, options) {
                    if (type === 'keydown' || type === 'keypress' || type === 'keyup') {
                        const modifiedListener = function(event) {
                            // Add small random delay to mimic human typing
                            setTimeout(() => {
                                listener.apply(this, arguments);
                            }, Math.random() * 50 + 10);
                        };
                        return originalAddEventListener.call(this, type, modifiedListener, options);
                    }
                    return originalAddEventListener.call(this, type, listener, options);
                };
            })();
            """
        ]
        
        for script in human_scripts:
            try:
                driver.execute_script(script)
            except:
                pass
    
    @staticmethod
    def _modify_navigator_properties(driver):
        """Modify navigator properties to appear more human-like"""
        # Use variable browser plugins and MIME types
        plugins_script = """
        // Define realistic plugin data
        const plugins = [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Portable Document Format'},
            {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
        ];
        
        // Define MIME types
        const mimeTypes = [
            {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
            {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'},
            {type: 'application/x-nacl', suffixes: '', description: 'Native Client Executable'},
            {type: 'application/x-pnacl', suffixes: '', description: 'Portable Native Client Executable'}
        ];
        
        // Override navigator.plugins
        Object.defineProperty(navigator, 'plugins', {
            get: function() {
                const pluginArray = [];
                
                // Add plugins
                for (let i = 0; i < plugins.length; i++) {
                    const plugin = {
                        name: plugins[i].name,
                        filename: plugins[i].filename,
                        description: plugins[i].description,
                        length: 1
                    };
                    
                    // Add item accessor
                    plugin[0] = {
                        type: mimeTypes[i].type,
                        description: mimeTypes[i].description,
                        suffixes: mimeTypes[i].suffixes,
                        enabledPlugin: plugin
                    };
                    
                    // Add to array
                    Object.defineProperty(pluginArray, '' + i, {
                        value: plugin,
                        enumerable: true
                    });
                    
                    // Add named property
                    Object.defineProperty(pluginArray, plugin.name, {
                        value: plugin,
                        enumerable: false
                    });
                }
                
                // Set length
                Object.defineProperty(pluginArray, 'length', {
                    value: plugins.length,
                    enumerable: false
                });
                
                // Add necessary functions
                pluginArray.item = function(index) {
                    return this[index] || null;
                };
                
                pluginArray.namedItem = function(name) {
                    return this[name] || null;
                };
                
                return pluginArray;
            }
        });
        
        // Override navigator.mimeTypes
        Object.defineProperty(navigator, 'mimeTypes', {
            get: function() {
                const mimeTypesArray = [];
                
                // Add mime types
                for (let i = 0; i < mimeTypes.length; i++) {
                    const mimeType = {
                        type: mimeTypes[i].type,
                        description: mimeTypes[i].description,
                        suffixes: mimeTypes[i].suffixes,
                        enabledPlugin: {}  // Will be populated in a real browser
                    };
                    
                    // Add to array
                    Object.defineProperty(mimeTypesArray, '' + i, {
                        value: mimeType,
                        enumerable: true
                    });
                    
                    // Add named property
                    Object.defineProperty(mimeTypesArray, mimeType.type, {
                        value: mimeType,
                        enumerable: false
                    });
                }
                
                // Set length
                Object.defineProperty(mimeTypesArray, 'length', {
                    value: mimeTypes.length,
                    enumerable: false
                });
                
                // Add necessary functions
                mimeTypesArray.item = function(index) {
                    return this[index] || null;
                };
                
                mimeTypesArray.namedItem = function(name) {
                    return this[name] || null;
                };
                
                return mimeTypesArray;
            }
        });
        """
        
        driver.execute_script(plugins_script)
    
    @staticmethod
    def _inject_visual_features(driver):
        """Inject visual features that Instagram uses to detect bots"""
        visual_script = """
        (function() {
            // Add CSS for scroll bar - Instagram might check CSS properties
            const style = document.createElement('style');
            style.textContent = `
                ::-webkit-scrollbar {
                    width: ${Math.floor(Math.random() * 3) + 10}px;
                }
                ::-webkit-scrollbar-track {
                    background: #f1f1f1;
                }
                ::-webkit-scrollbar-thumb {
                    background: #888;
                }
                ::-webkit-scrollbar-thumb:hover {
                    background: #555;
                }
            `;
            document.head.appendChild(style);
            
            // Instagram checks for cursor behavior
            document.addEventListener('mousemove', function(e) {
                // Create a ripple effect on mouse move (creates DOM changes)
                if (Math.random() < 0.001) { // Very rare to avoid disrupting normal use
                    const ripple = document.createElement('div');
                    ripple.style.position = 'fixed';
                    ripple.style.width = '5px';
                    ripple.style.height = '5px';
                    ripple.style.backgroundColor = 'transparent';
                    ripple.style.borderRadius = '50%';
                    ripple.style.pointerEvents = 'none';
                    ripple.style.left = e.clientX + 'px';
                    ripple.style.top = e.clientY + 'px';
                    ripple.style.zIndex = '9999';
                    document.body.appendChild(ripple);
                    
                    // Remove it after a short time
                    setTimeout(() => {
                        if (document.body.contains(ripple)) {
                            document.body.removeChild(ripple);
                        }
                    }, 100);
                }
            });
        })();
        """
        
        driver.execute_script(visual_script)
class InstagramAccountCreator:
    """Service for creating new Instagram accounts with verification handling"""
    
    def __init__(self, account_service, proxy_manager=None, captcha_solver=None, email_verifier=None):
        self.account_service = account_service
        self.browser = InstagramBrowser()
        self.proxy_manager = proxy_manager or ProxyManager()
        self.captcha_solver = captcha_solver or CaptchaSolver()
        self.email_verifier = email_verifier or EmailVerifier()
        self.logger = logging.getLogger(__name__)
        
        # Define delays (in seconds) for human-like behavior
        self.delays = {
            'typing': (0.1, 0.3),        # Delay between keypresses
            'field_change': (0.5, 1.5),  # Delay between fields
            'page_load': (2, 4),         # Delay after page loads
            'verification': (10, 15)     # Delay for verification process
        }
        
        # Account creation statistics
        self.stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'verifications_required': 0,
            'captchas_encountered': 0
        }
        
        # Thread lock for stats
        self.stats_lock = threading.Lock()
        
        # Callbacks
        self.progress_callback = None
        self.status_callback = None

    def set_callbacks(self, progress_callback=None, status_callback=None):
        """Set callbacks for UI updates"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
    
    def _update_status(self, message):
        """Update status in UI if callback is set"""
        if self.status_callback:
            self.status_callback(message)
        self.logger.info(message)
    
    def _update_progress(self, current_step, total_steps):
        """Update progress in UI if callback is set"""
        if self.progress_callback:
            progress = (current_step / total_steps) * 100
            self.progress_callback(progress)
    
    def _random_delay(self, delay_type='typing'):
        """Add random delay between actions for human-like behavior"""
        min_delay, max_delay = self.delays.get(delay_type, (0.5, 1.5))
        time.sleep(random.uniform(min_delay, max_delay))
    
    def _human_type(self, element, text):
        """Type text with human-like delays including occasional mistakes and corrections"""
        for i, char in enumerate(text):
            # Occasionally make a typo (1% chance) but not on the first or last character
            if i > 0 and i < len(text) - 1 and random.random() < 0.01:
                # Type a random wrong key that's adjacent on keyboard
                adjacent_keys = {
                    'a': 'sqzw', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wrsdf',
                    'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'uojk', 'j': 'huikmn',
                    'k': 'jiolm', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
                    'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'qazxcdew', 't': 'rfgy',
                    'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
                    'z': 'asx', '0': '9', '1': '2', '2': '13', '3': '24', '4': '35',
                    '5': '46', '6': '57', '7': '68', '8': '79', '9': '80'
                }
                
                if char.lower() in adjacent_keys:
                    wrong_key = random.choice(adjacent_keys[char.lower()])
                    element.send_keys(wrong_key)
                    time.sleep(random.uniform(0.1, 0.3))
                    
                    # Send backspace and pause briefly
                    element.send_keys('\b')
                    time.sleep(random.uniform(0.2, 0.5))
            
            # Type the correct character
            element.send_keys(char)
            
            # Occasionally pause (5% chance)
            if random.random() < 0.05:
                time.sleep(random.uniform(0.5, 1.5))
            else:
                # Regular typing delay
                time.sleep(random.uniform(0.05, 0.25))
    
    def check_username_available(self, username):
        """Check if a username is available on Instagram"""
        self._update_status(f"Checking availability for username: {username}")
        
        driver = None
        try:
            # Create a driver with a fresh session
            driver = self.browser._create_driver(fresh_session=True)
            
            # Go to Instagram signup page
            driver.get("https://www.instagram.com/accounts/emailsignup/")
            self._random_delay('page_load')
            
            # Close any cookies dialog if present
            try:
                cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self._random_delay('field_change')
            except:
                pass
            
            # Find and fill username field
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            self._human_type(username_field, username)
            self._random_delay('field_change')
            
            # Wait for availability check to complete
            time.sleep(2)
            
            # Check for error messages
            error_messages = driver.find_elements(By.XPATH, "//span[contains(@class, 'error') or contains(@class, 'coreSpriteInputError')]")
            for error in error_messages:
                if "username" in error.text.lower() and ("taken" in error.text.lower() or "available" in error.text.lower()):
                    if "not available" in error.text.lower() or "taken" in error.text.lower():
                        self._update_status(f"Username '{username}' is not available")
                        return False
            
            # If no error messages about username, assume it's available
            self._update_status(f"Username '{username}' appears to be available")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking username availability: {str(e)}")
            return False
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def generate_username(self, fullname, prefix=None, suffix=None):
        """Generate a username based on full name with optional prefix/suffix"""
        # Clean and simplify full name
        simple_name = re.sub(r'[^a-zA-Z0-9]', '', fullname.lower())
        
        # Generate username variations
        variations = []
        
        # Use first name
        if len(simple_name) >= 3:
            first_name = simple_name[:simple_name.find(' ')] if ' ' in simple_name else simple_name
            
            # Basic variations
            variations.append(first_name)
            variations.append(f"{first_name}{random.randint(1, 9999)}")
            
            # With prefix if provided
            if prefix:
                variations.append(f"{prefix}{first_name}")
                variations.append(f"{prefix}_{first_name}")
                variations.append(f"{prefix}.{first_name}")
                
            # With suffix if provided
            if suffix:
                variations.append(f"{first_name}{suffix}")
                variations.append(f"{first_name}_{suffix}")
                variations.append(f"{first_name}.{suffix}")
                
            # With both if provided
            if prefix and suffix:
                variations.append(f"{prefix}{first_name}{suffix}")
        
        # Add some random variations if we don't have enough
        while len(variations) < 5:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            variations.append(f"{simple_name}{random_suffix}")
        
        # Shuffle variations for randomness
        random.shuffle(variations)
        
        return variations
    
    def _handle_captcha(self, driver):
        """Handle any CAPTCHA challenges that appear during account creation"""
        try:
            # Look for common CAPTCHA indicators
            captcha_indicators = [
                "//img[contains(@src, 'captcha')]",
                "//div[contains(text(), 'captcha') or contains(text(), 'CAPTCHA')]",
                "//iframe[contains(@src, 'recaptcha') or contains(@src, 'hcaptcha')]"
            ]
            
            captcha_found = False
            for indicator in captcha_indicators:
                elements = driver.find_elements(By.XPATH, indicator)
                if elements:
                    captcha_found = True
                    break
            
            if not captcha_found:
                return True
            
            # Update stats
            with self.stats_lock:
                self.stats['captchas_encountered'] += 1
            
            self._update_status("CAPTCHA detected. Attempting to solve...")
            
            # Check for reCAPTCHA v2
            recaptcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
            if recaptcha_frames:
                return self.captcha_solver.solve_recaptcha(driver, recaptcha_frames[0])
            
            # Check for hCaptcha
            hcaptcha_frames = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'hcaptcha')]")
            if hcaptcha_frames:
                return self.captcha_solver.solve_hcaptcha(driver, hcaptcha_frames[0])
            
            # Generic image captcha
            image_captchas = driver.find_elements(By.XPATH, "//img[contains(@src, 'captcha')]")
            if image_captchas:
                captcha_input = driver.find_element(By.XPATH, "//input[@id='captcha' or contains(@name, 'captcha')]")
                if captcha_input:
                    captcha_url = image_captchas[0].get_attribute('src')
                    solution = self.captcha_solver.solve_image_captcha(captcha_url)
                    if solution:
                        self._human_type(captcha_input, solution)
                        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                        submit_button.click()
                        self._random_delay('verification')
                        return True
            
            self._update_status("Failed to automatically solve CAPTCHA")
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling CAPTCHA: {str(e)}")
            return False
    
    def _verify_email(self, driver, email_address):
        """Handle email verification process"""
        self._update_status(f"Waiting for email verification code for {email_address}")
        
        try:
            # Wait for the verification input field to appear
            verification_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'verification') or contains(@name, 'confirm') or contains(@aria-label, 'Confirmation')]"))
            )
            
            # Update stats
            with self.stats_lock:
                self.stats['verifications_required'] += 1
            
            # Wait for verification code to be retrieved
            verification_code = self.email_verifier.get_verification_code(email_address, max_wait=60)
            
            if not verification_code:
                self._update_status("Failed to retrieve verification code")
                return False
            
            self._update_status(f"Verification code received: {verification_code}")
            
            # Enter verification code
            verification_input.clear()
            self._human_type(verification_input, verification_code)
            
            # Find and click the submit button
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Confirm') or contains(text(), 'Next') or contains(text(), 'Verify')]")
            submit_button.click()
            
            # Wait for verification to be processed
            self._random_delay('verification')
            
            # Check for error messages
            error_elements = driver.find_elements(By.XPATH, "//p[contains(@class, 'error') or contains(text(), 'incorrect') or contains(text(), 'wrong')]")
            if error_elements:
                self._update_status(f"Verification failed: {error_elements[0].text}")
                return False
            
            self._update_status("Email verification successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during email verification: {str(e)}")
            return False
    
    def _verify_phone(self, driver, phone_number):
        """Handle phone verification if required"""
        self._update_status(f"Phone verification requested for {phone_number}")
        
        try:
            # Wait for the SMS code input field
            sms_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'sms_code') or contains(@aria-label, 'Confirmation')]"))
            )
            
            # Update stats
            with self.stats_lock:
                self.stats['verifications_required'] += 1
            
            # This would typically use an SMS verification service
            # For now, we'll prompt the user to enter the code manually
            self._update_status("⚠️ SMS verification required. Please check UI for manual entry.")
            
            # Here you would integrate with your SMS verification service
            # sms_code = self.sms_service.get_verification_code(phone_number)
            
            # Since we're likely awaiting manual input from the UI, 
            # we'll return True and handle the actual verification elsewhere
            return True
            
        except Exception as e:
            self.logger.error(f"Error during phone verification: {str(e)}")
            return False
    
    def _complete_profile(self, driver, username, profile_pic=None, bio=None):
        """Complete the profile setup steps after account creation"""
        self._update_status("Completing profile setup")
        
        try:
            # Skip "Find Friends" step if present
            try:
                skip_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Skip') or contains(text(), 'Not Now')]")
                if skip_buttons:
                    skip_buttons[0].click()
                    self._random_delay('field_change')
            except:
                pass
            
            # Upload profile picture if provided
            if profile_pic:
                try:
                    # Find the profile picture upload button
                    upload_buttons = driver.find_elements(By.XPATH, "//input[@type='file'] | //button[contains(text(), 'picture') or contains(text(), 'photo') or contains(text(), 'avatar')]")
                    
                    if upload_buttons:
                        if upload_buttons[0].tag_name == 'input':
                            # Direct file input
                            upload_buttons[0].send_keys(profile_pic)
                        else:
                            # Click button, then find file input
                            upload_buttons[0].click()
                            self._random_delay('field_change')
                            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
                            file_input.send_keys(profile_pic)
                        
                        self._random_delay('field_change')
                        
                        # Look for crop/save button
                        save_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Save') or contains(text(), 'Apply') or contains(text(), 'Done')]")
                        if save_buttons:
                            save_buttons[0].click()
                            self._random_delay('field_change')
                except Exception as pic_error:
                    self.logger.warning(f"Error uploading profile picture: {str(pic_error)}")
            
            # Add bio if provided
            if bio:
                try:
                    # Navigate to edit profile page
                    driver.get(f"https://www.instagram.com/{username}/edit/")
                    self._random_delay('page_load')
                    
                    # Find bio field and enter text
                    bio_fields = driver.find_elements(By.XPATH, "//textarea[@name='biography' or contains(@aria-label, 'Bio')]")
                    if bio_fields:
                        bio_fields[0].clear()
                        self._human_type(bio_fields[0], bio)
                        
                        # Find and click submit button
                        submit_button = driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Submit') or contains(text(), 'Save')]")
                        submit_button.click()
                        self._random_delay('field_change')
                except Exception as bio_error:
                    self.logger.warning(f"Error adding bio: {str(bio_error)}")
            
            self._update_status("Profile setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error completing profile: {str(e)}")
            return False
    
    def create_account(self, email, fullname, username, password, phone=None, 
                   date_of_birth=None, gender=None, profile_pic=None, bio=None):
        """
        Create a new Instagram account with the given details
        
        Args:
            email (str): Email address for account
            fullname (str): Full name for profile
            username (str): Desired username
            password (str): Password for account
            phone (str, optional): Phone number for verification
            date_of_birth (tuple, optional): Tuple of (month, day, year)
            gender (str, optional): Gender ('Male', 'Female', or 'Custom')
            profile_pic (str, optional): Path to profile picture
            bio (str, optional): Biography text
            
        Returns:
            dict: Result with success status and details
        """
        # Update stats
        with self.stats_lock:
            self.stats['attempts'] += 1
        
        proxy = None
        driver = None
        result = {
            'success': False,
            'username': username,
            'error': None,
            'verification_required': False,
            'verification_type': None
        }
        
        try:
            self._update_status(f"Starting account creation for {username}")
            self._update_progress(1, 10)
            
            # Get a proxy if available
            proxy = self.proxy_manager.get_proxy()
            
            # Create a fresh browser instance
            if proxy:
                self._update_status(f"Using proxy: {proxy.get('ip')}:{proxy.get('port')}")
                driver = self.browser._create_driver(proxy=proxy, fresh_session=True)
            else:
                driver = self.browser._create_driver(fresh_session=True)
            
            # IMPROVED: Natural navigation flow instead of direct URL
            # First navigate to Instagram home page
            driver.get("https://www.instagram.com/")
            self._random_delay('page_load')
            self._update_progress(2, 10)
            
            # Close any cookies dialog if present
            try:
                cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self._random_delay('field_change')
            except Exception as e:
                self.logger.warning(f"No cookie dialog or error handling it: {str(e)}")
            
            # Look for sign up link on the homepage
            try:
                signup_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'emailsignup') or contains(text(), 'Sign up') or contains(text(), 'Create account')]")
                if signup_links:
                    # Use JavaScript click which is more reliable
                    driver.execute_script("arguments[0].click();", signup_links[0])
                    self._update_status("Clicked sign up link")
                else:
                    # Fallback: direct navigation but with referrer
                    self._update_status("No signup link found, trying direct navigation")
                    driver.execute_script("window.location.href = 'https://www.instagram.com/accounts/emailsignup/';")
                
                self._random_delay('page_load')
            except Exception as e:
                self.logger.warning(f"Error finding or clicking signup link: {str(e)}")
                # Fallback approach
                self._update_status("Using alternate navigation approach")
                driver.get("https://www.instagram.com/")
                self._random_delay('page_load')
                driver.execute_script("window.location.href = 'https://www.instagram.com/accounts/emailsignup/';")
                self._random_delay('page_load')
            
            # Verify we reached the signup page
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Look for any signup form elements
                    email_field = driver.find_element(By.NAME, "emailOrPhone")
                    if email_field:
                        self._update_status("Successfully reached signup page")
                        break
                except:
                    if attempt < max_attempts - 1:
                        self._update_status(f"Signup page not loaded correctly, retrying ({attempt+1}/{max_attempts})")
                        # Try refreshing
                        driver.refresh()
                        self._random_delay('page_load')
                    else:
                        raise Exception("Failed to load signup page after multiple attempts")
            
            # CONTINUE WITH EXISTING SIGNUP FLOW...
            # Fill out the signup form
            # Email field
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "emailOrPhone"))
            )
            email_field.clear()
            self._human_type(email_field, email)
            self._random_delay('field_change')
            self._update_progress(3, 10)
            
            # Full name field
            fullname_field = driver.find_element(By.NAME, "fullName")
            fullname_field.clear()
            self._human_type(fullname_field, fullname)
            self._random_delay('field_change')
            self._update_progress(4, 10)
            
            # Username field
            username_field = driver.find_element(By.NAME, "username")
            username_field.clear()
            self._human_type(username_field, username)
            self._random_delay('field_change')
            self._update_progress(5, 10)
            
            # Password field
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            self._human_type(password_field, password)
            self._random_delay('field_change')
            self._update_progress(6, 10)
            
            # Date of birth if provided
            if date_of_birth:
                month, day, year = date_of_birth
                
                # Try different selectors for date fields
                try:
                    # Look for select fields
                    month_select = driver.find_element(By.XPATH, "//select[contains(@name, 'month') or contains(@aria-label, 'Month')]")
                    day_select = driver.find_element(By.XPATH, "//select[contains(@name, 'day') or contains(@aria-label, 'Day')]")
                    year_select = driver.find_element(By.XPATH, "//select[contains(@name, 'year') or contains(@aria-label, 'Year')]")
                    
                    # Select options
                    month_select.send_keys(str(month))
                    self._random_delay('field_change')
                    day_select.send_keys(str(day))
                    self._random_delay('field_change')
                    year_select.send_keys(str(year))
                    self._random_delay('field_change')
                except:
                    # Alternative approach if select fields not found
                    self.logger.warning("Date of birth select fields not found, trying alternative approach")
                    
                    # Look for birthday link/button
                    try:
                        birthday_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Birthday')]")
                        if birthday_buttons:
                            birthday_buttons[0].click()
                            self._random_delay('field_change')
                            
                            # Fill in the date fields
                            date_inputs = driver.find_elements(By.XPATH, "//input[@type='text']")
                            if len(date_inputs) >= 3:
                                # Month
                                date_inputs[0].clear()
                                self._human_type(date_inputs[0], str(month))
                                self._random_delay('field_change')
                                
                                # Day
                                date_inputs[1].clear()
                                self._human_type(date_inputs[1], str(day))
                                self._random_delay('field_change')
                                
                                # Year
                                date_inputs[2].clear()
                                self._human_type(date_inputs[2], str(year))
                                self._random_delay('field_change')
                                
                                # Submit
                                next_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Submit')]")
                                if next_buttons:
                                    next_buttons[0].click()
                                    self._random_delay('field_change')
                    except:
                        pass
            
            # Gender selection if provided
            if gender:
                try:
                    gender_options = {
                        'male': "//label[contains(text(), 'Male')]",
                        'female': "//label[contains(text(), 'Female')]",
                        'custom': "//label[contains(text(), 'Custom') or contains(text(), 'Prefer not to say')]"
                    }
                    
                    gender_xpath = gender_options.get(gender.lower())
                    if gender_xpath:
                        gender_element = driver.find_element(By.XPATH, gender_xpath)
                        gender_element.click()
                        self._random_delay('field_change')
                except:
                    self.logger.warning("Gender selection not found or not required")
            
            self._update_progress(7, 10)
            
            # Submit the form
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            self._random_delay('page_load')
            self._update_progress(8, 10)
            
            # Handle any CAPTCHA challenge
            captcha_result = self._handle_captcha(driver)
            if not captcha_result:
                self._update_status("CAPTCHA challenge failed")
                result['error'] = "CAPTCHA verification failed"
                return result
            
            # Check for errors
            error_elements = driver.find_elements(By.XPATH, "//p[contains(@class, 'error')] | //span[contains(@class, 'coreSpriteInputError')]")
            if error_elements:
                error_message = error_elements[0].text
                self._update_status(f"Error during signup: {error_message}")
                result['error'] = error_message
                
                # Update stats
                with self.stats_lock:
                    self.stats['failures'] += 1
                return result
            
            # Check for email verification requirement
            if "verification" in driver.current_url.lower() or "confirm" in driver.current_url.lower():
                self._update_status("Email verification required")
                result['verification_required'] = True
                result['verification_type'] = 'email'
                
                # Handle email verification
                email_verified = self._verify_email(driver, email)
                if not email_verified:
                    self._update_status("Email verification failed")
                    result['error'] = "Email verification failed"
                    
                    # Update stats
                    with self.stats_lock:
                        self.stats['failures'] += 1
                    return result
            
            # Check for phone verification requirement
            phone_elements = driver.find_elements(By.XPATH, "//input[@name='phone_number'] | //input[contains(@aria-label, 'Phone')]")
            if phone_elements:
                self._update_status("Phone verification required")
                result['verification_required'] = True
                result['verification_type'] = 'phone'
                
                if phone:
                    # Fill in phone number
                    phone_field = phone_elements[0]
                    phone_field.clear()
                    self._human_type(phone_field, phone)
                    
                    # Submit phone number
                    next_buttons = driver.find_elements(By.XPATH, "//button[@type='submit' or contains(text(), 'Next')]")
                    if next_buttons:
                        next_buttons[0].click()
                        self._random_delay('field_change')
                        
                        # Handle phone verification
                        phone_verified = self._verify_phone(driver, phone)
                        if not phone_verified:
                            self._update_status("Phone verification failed")
                            result['error'] = "Phone verification failed"
                            
                            # Update stats
                            with self.stats_lock:
                                self.stats['failures'] += 1
                            return result
                else:
                    self._update_status("Phone verification required but no phone number provided")
                    result['error'] = "Phone verification required but no phone number provided"
                    
                    # Update stats
                    with self.stats_lock:
                        self.stats['failures'] += 1
                    return result
            
            self._update_progress(9, 10)
            
            # Complete profile setup
            profile_complete = self._complete_profile(driver, username, profile_pic, bio)
            
            # Save cookies
            if self.browser._save_cookies(driver, username):
                self._update_status("Session cookies saved successfully")
            else:
                self._update_status("Warning: Failed to save session cookies")
            
            # Add account to database
            try:
                self.account_service.add_account(username, password)
                self._update_status(f"Account {username} added to database")
            except Exception as db_error:
                self._update_status(f"Warning: Failed to add account to database: {str(db_error)}")
            
            self._update_progress(10, 10)
            self._update_status(f"Account {username} created successfully")
            
            # Update stats
            with self.stats_lock:
                self.stats['successes'] += 1
            
            result['success'] = True
            return result
            
        except Exception as e:
            self.logger.error(f"Account creation failed: {str(e)}")
            result['error'] = str(e)
            
            # Update stats
            with self.stats_lock:
                self.stats['failures'] += 1
            
            return result
            
        finally:
            # Release proxy if used
            if proxy:
                self.proxy_manager.release_proxy(proxy.get('id'))
            
            # Close browser
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def get_stats(self):
        """Get current account creation statistics"""
        with self.stats_lock:
            return self.stats.copy()