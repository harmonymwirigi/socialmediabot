# app/utils/captcha_solver.py

import time
import logging
import requests
import base64
import io
import os
import re
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CaptchaSolver:
    """
    Handles CAPTCHA solving for Instagram account creation
    Supports both manual and automated solutions
    """
    
    def __init__(self, captcha_service=None):
        self.logger = logging.getLogger(__name__)
        self.captcha_service = captcha_service
        self.lock = threading.Lock()
    
    def solve_recaptcha(self, driver, iframe):
        """
        Solve Google reCAPTCHA v2
        
        Args:
            driver: Selenium WebDriver
            iframe: reCAPTCHA iframe element
            
        Returns:
            bool: Whether solving was successful
        """
        try:
            self.logger.info("Attempting to solve reCAPTCHA")
            
            if self.captcha_service:
                return self._solve_recaptcha_with_api(driver, iframe)
            else:
                return self._solve_recaptcha_manually(driver, iframe)
                
        except Exception as e:
            self.logger.error(f"Error solving reCAPTCHA: {str(e)}")
            return False
    
    def _solve_recaptcha_with_api(self, driver, iframe):
        """Use external API to solve reCAPTCHA"""
        try:
            # Get site key
            if not iframe:
                self.logger.error("No reCAPTCHA iframe found")
                return False
            
            iframe_src = iframe.get_attribute('src')
            site_key_match = re.search(r'k=([^&]+)', iframe_src)
            
            if not site_key_match:
                self.logger.error("Could not find site key in iframe source")
                return False
            
            site_key = site_key_match.group(1)
            page_url = driver.current_url
            
            # Submit to CAPTCHA solving service
            api_key = self.captcha_service.get('api_key')
            api_url = self.captcha_service.get('api_url')
            
            self.logger.info(f"Submitting reCAPTCHA to solving service: {site_key}")
            
            # Create task
            data = {
                "clientKey": api_key,
                "task": {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key
                }
            }
            
            response = requests.post(f"{api_url}/createTask", json=data)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to create CAPTCHA task: {response.text}")
                return False
            
            task_id = response.json().get('taskId')
            
            if not task_id:
                self.logger.error("No task ID returned from CAPTCHA service")
                return False
            
            # Wait for solution
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(5)  # Wait between checks
                
                data = {
                    "clientKey": api_key,
                    "taskId": task_id
                }
                
                response = requests.post(f"{api_url}/getTaskResult", json=data)
                
                if response.status_code != 200:
                    self.logger.error(f"Error checking CAPTCHA solution: {response.text}")
                    continue
                
                result = response.json()
                status = result.get('status')
                
                if status == 'ready':
                    solution = result.get('solution', {}).get('gRecaptchaResponse')
                    if solution:
                        # Execute JavaScript to set the solution
                        js_code = f"""
                        document.getElementById('g-recaptcha-response').innerHTML = '{solution}';
                        """
                        
                        # Switch to main content
                        driver.switch_to.default_content()
                        
                        # Execute the JavaScript
                        driver.execute_script(js_code)
                        
                        # Submit the form
                        submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")
                        if submit_buttons:
                            submit_buttons[0].click()
                            time.sleep(2)
                            return True
                        
                        return True
                    
                elif status == 'processing':
                    continue
                    
                else:
                    self.logger.error(f"CAPTCHA solving failed with status: {status}")
                    return False
            
            self.logger.error("CAPTCHA solving timed out")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in API CAPTCHA solving: {str(e)}")
            return False
    
    def _solve_recaptcha_manually(self, driver, iframe):
        """
        Manual approach for solving reCAPTCHA
        This simply clicks the checkbox and waits for potential verification
        """
        try:
            # Switch to reCAPTCHA iframe
            driver.switch_to.frame(iframe)
            
            # Find the checkbox
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
            )
            
            # Click the checkbox
            checkbox.click()
            
            # Wait for verification to complete automatically
            # This won't work if there's an image verification challenge
            time.sleep(5)
            
            # Check if the checkbox is checked
            is_checked = driver.execute_script(
                "return document.getElementById('recaptcha-anchor').getAttribute('aria-checked') === 'true';"
            )
            
            # Switch back to main content
            driver.switch_to.default_content()
            
            if is_checked:
                self.logger.info("reCAPTCHA checkbox checked successfully")
                return True
            else:
                self.logger.warning("reCAPTCHA verification may require image challenge")
                # Most likely requires image verification which we can't automate easily
                return False
                
        except Exception as e:
            self.logger.error(f"Error in manual reCAPTCHA solving: {str(e)}")
            driver.switch_to.default_content()  # Ensure we switch back to main content
            return False
    
    def solve_hcaptcha(self, driver, iframe):
        """
        Solve hCaptcha
        
        Args:
            driver: Selenium WebDriver
            iframe: hCaptcha iframe element
            
        Returns:
            bool: Whether solving was successful
        """
        try:
            self.logger.info("Attempting to solve hCaptcha")
            
            if self.captcha_service:
                return self._solve_hcaptcha_with_api(driver, iframe)
            else:
                return self._solve_hcaptcha_manually(driver, iframe)
                
        except Exception as e:
            self.logger.error(f"Error solving hCaptcha: {str(e)}")
            return False
    
    def _solve_hcaptcha_with_api(self, driver, iframe):
        """Use external API to solve hCaptcha"""
        try:
            # Get site key
            if not iframe:
                self.logger.error("No hCaptcha iframe found")
                return False
            
            iframe_src = iframe.get_attribute('src')
            site_key_match = re.search(r'sitekey=([^&]+)', iframe_src)
            
            if not site_key_match:
                self.logger.error("Could not find site key in iframe source")
                return False
            
            site_key = site_key_match.group(1)
            page_url = driver.current_url
            
            # Submit to CAPTCHA solving service
            api_key = self.captcha_service.get('api_key')
            api_url = self.captcha_service.get('api_url')
            
            self.logger.info(f"Submitting hCaptcha to solving service: {site_key}")
            
            # Create task
            data = {
                "clientKey": api_key,
                "task": {
                    "type": "HCaptchaTaskProxyless",
                    "websiteURL": page_url,
                    "websiteKey": site_key
                }
            }
            
            response = requests.post(f"{api_url}/createTask", json=data)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to create CAPTCHA task: {response.text}")
                return False
            
            task_id = response.json().get('taskId')
            
            if not task_id:
                self.logger.error("No task ID returned from CAPTCHA service")
                return False
            
            # Wait for solution
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(5)  # Wait between checks
                
                data = {
                    "clientKey": api_key,
                    "taskId": task_id
                }
                
                response = requests.post(f"{api_url}/getTaskResult", json=data)
                
                if response.status_code != 200:
                    self.logger.error(f"Error checking CAPTCHA solution: {response.text}")
                    continue
                
                result = response.json()
                status = result.get('status')
                
                if status == 'ready':
                    solution = result.get('solution', {}).get('token')
                    if solution:
                        # Execute JavaScript to set the solution
                        js_code = f"""
                        document.querySelector('textarea[name="h-captcha-response"]').innerHTML = '{solution}';
                        document.querySelector('input[name="h-captcha-response"]').value = '{solution}';
                        """
                        
                        # Switch to main content
                        driver.switch_to.default_content()
                        
                        # Execute the JavaScript
                        driver.execute_script(js_code)
                        
                        # Submit the form
                        submit_buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")
                        if submit_buttons:
                            submit_buttons[0].click()
                            time.sleep(2)
                            return True
                        
                        return True
                    
                elif status == 'processing':
                    continue
                    
                else:
                    self.logger.error(f"CAPTCHA solving failed with status: {status}")
                    return False
            
            self.logger.error("CAPTCHA solving timed out")
            return False
            
        except Exception as e:
            self.logger.error(f"Error in API hCaptcha solving: {str(e)}")
            return False
    
    def _solve_hcaptcha_manually(self, driver, iframe):
        """
        Manual approach for solving hCaptcha
        This simply clicks the checkbox and waits for potential verification
        """
        try:
            # Switch to hCaptcha iframe
            driver.switch_to.frame(iframe)
            
            # Find the checkbox
            checkbox = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "checkbox"))
            )
            
            # Click the checkbox
            checkbox.click()
            
            # Wait for verification to complete automatically
            # This won't work if there's an image verification challenge
            time.sleep(5)
            
            # Check if the checkbox is checked
            is_checked = driver.execute_script(
                "return document.getElementById('checkbox').getAttribute('aria-checked') === 'true';"
            )
            
            # Switch back to main content
            driver.switch_to.default_content()
            
            if is_checked:
                self.logger.info("hCaptcha checkbox checked successfully")
                return True
            else:
                self.logger.warning("hCaptcha verification may require image challenge")
                # Most likely requires image verification which we can't automate easily
                return False
                
        except Exception as e:
            self.logger.error(f"Error in manual hCaptcha solving: {str(e)}")
            driver.switch_to.default_content()  # Ensure we switch back to main content
            return False
    
    def solve_image_captcha(self, captcha_url):
        """
        Solve a simple image CAPTCHA
        
        Args:
            captcha_url (str): URL of the CAPTCHA image
            
        Returns:
            str: CAPTCHA solution or None if failed
        """
        try:
            self.logger.info(f"Attempting to solve image CAPTCHA: {captcha_url}")
            
            if self.captcha_service:
                return self._solve_image_captcha_with_api(captcha_url)
            else:
                self.logger.warning("No CAPTCHA service configured for image CAPTCHA")
                return None
                
        except Exception as e:
            self.logger.error(f"Error solving image CAPTCHA: {str(e)}")
            return None
    
    def _solve_image_captcha_with_api(self, captcha_url):
        """Use external API to solve image CAPTCHA"""
        try:
            # Download the image
            response = requests.get(captcha_url)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to download CAPTCHA image: {response.status_code}")
                return None
            
            # Get image data as base64
            image_data = base64.b64encode(response.content).decode('utf-8')
            
            # Submit to CAPTCHA solving service
            api_key = self.captcha_service.get('api_key')
            api_url = self.captcha_service.get('api_url')
            
            self.logger.info("Submitting image CAPTCHA to solving service")
            
            # Create task
            data = {
                "clientKey": api_key,
                "task": {
                    "type": "ImageToTextTask",
                    "body": image_data
                }
            }
            
            response = requests.post(f"{api_url}/createTask", json=data)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to create CAPTCHA task: {response.text}")
                return None
            
            task_id = response.json().get('taskId')
            
            if not task_id:
                self.logger.error("No task ID returned from CAPTCHA service")
                return None
            
            # Wait for solution
            max_attempts = 15
            for attempt in range(max_attempts):
                time.sleep(3)  # Wait between checks
                
                data = {
                    "clientKey": api_key,
                    "taskId": task_id
                }
                
                response = requests.post(f"{api_url}/getTaskResult", json=data)
                
                if response.status_code != 200:
                    self.logger.error(f"Error checking CAPTCHA solution: {response.text}")
                    continue
                
                result = response.json()
                status = result.get('status')
                
                if status == 'ready':
                    solution = result.get('solution', {}).get('text')
                    if solution:
                        self.logger.info(f"CAPTCHA solved: {solution}")
                        return solution
                    
                elif status == 'processing':
                    continue
                    
                else:
                    self.logger.error(f"CAPTCHA solving failed with status: {status}")
                    return None
            
            self.logger.error("CAPTCHA solving timed out")
            return None
            
        except Exception as e:
            self.logger.error(f"Error in API image CAPTCHA solving: {str(e)}")
            return None