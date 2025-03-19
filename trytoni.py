from selenium import webdriver
import os

def create_driver_with_custom_profile():
    """Create a Chrome driver with a dedicated user profile to maintain session persistence."""
    options = webdriver.ChromeOptions()
    
    # Define a custom user profile directory for Selenium
    selenium_profile = os.path.expanduser("~") + "/selenium_profile"
    os.makedirs(selenium_profile, exist_ok=True)

    options.add_argument(f"user-data-dir={selenium_profile}")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=en-US")

    driver = webdriver.Chrome(options=options)
    return driver

# Create the browser with a dedicated Selenium profile
driver = create_driver_with_custom_profile()

# Navigate directly to the Instagram post (session remains active if previously logged in)
driver.get("https://www.instagram.com/reel/DFdlUzlIW4K/?utm_source=ig_web_copy_link")