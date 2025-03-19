# usage_example.py

import time
import logging
import os
from selenium import webdriver
from app.services.instagram.account_creator import InstagramAccountCreator
from app.services.instagram.account import InstagramAccountService
from app.utils.email_verifier import EmailVerifier
from app.utils.proxy_manager import ProxyManager
from app.utils.captcha_solver import CaptchaSolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_account_creation_with_inbox_lv():
    """Test Instagram account creation with inbox.lv email verification"""
    
    # Get credentials from environment or user input
    inbox_lv_email = os.environ.get('INBOX_LV_EMAIL') or input("Enter your inbox.lv email: ")
    inbox_lv_password = os.environ.get('INBOX_LV_PASSWORD') or input("Enter your inbox.lv password: ")
    
    # Initialize services
    account_service = InstagramAccountService()
    proxy_manager = ProxyManager()
    captcha_solver = CaptchaSolver()
    
    # Initialize email verifier with inbox.lv credentials
    email_verifier = EmailVerifier(
        inbox_lv_credentials={
            'email': inbox_lv_email,
            'password': inbox_lv_password
        }
    )
    
    # Initialize account creator
    account_creator = InstagramAccountCreator(
        account_service=account_service,
        proxy_manager=proxy_manager,
        captcha_solver=captcha_solver,
        email_verifier=email_verifier
    )
    
    # Progress callback
    def update_progress(progress):
        logger.info(f"Progress: {progress:.1f}%")
    
    # Status callback
    def update_status(message):
        logger.info(f"Status: {message}")
    
    # Set callbacks
    account_creator.set_callbacks(
        progress_callback=update_progress,
        status_callback=update_status
    )
    
    # Account details
    account_details = {
        'username': 'test_username_' + str(int(time.time())),
        'email': inbox_lv_email,  # Use your inbox.lv email
        'fullname': 'Test User',
        'password': 'TestPassword123!',
        'date_of_birth': (1, 1, 1990),  # January 1, 1990
        'gender': 'Female'
    }
    
    logger.info(f"Creating account with username: {account_details['username']}")
    
    try:
        # Start account creation
        result = account_creator.create_account(**account_details)
        
        # Check result
        if result['success']:
            logger.info(f"Account creation successful!")
            logger.info(f"Username: {result['username']}")
        else:
            logger.error(f"Account creation failed: {result.get('error')}")
            if result.get('verification_required'):
                logger.info(f"Verification type required: {result.get('verification_type')}")
    
    except Exception as e:
        logger.error(f"Error during account creation: {str(e)}")
    
    finally:
        # Clean up resources
        email_verifier.cleanup()
        logger.info("Test completed")

# Simplified test for just the email verification component
def test_email_verification():
    """Test only the email verification component with inbox.lv"""
    
    # Get credentials from environment or user input
    inbox_lv_email = os.environ.get('INBOX_LV_EMAIL') or input("Enter your inbox.lv email: ")
    inbox_lv_password = os.environ.get('INBOX_LV_PASSWORD') or input("Enter your inbox.lv password: ")
    
    # Initialize email verifier
    email_verifier = EmailVerifier(
        inbox_lv_credentials={
            'email': inbox_lv_email,
            'password': inbox_lv_password
        }
    )
    
    try:
        logger.info(f"Testing email verification for {inbox_lv_email}")
        
        # Check for verification code
        logger.info("Waiting for verification code...")
        code = email_verifier.get_verification_code(inbox_lv_email, max_wait=120)
        
        if code:
            logger.info(f"Found verification code: {code}")
        else:
            logger.warning("No verification code found")
            
            # At this point in a real scenario, you could:
            # 1. Trigger Instagram to send a new verification email
            # 2. Wait for a longer period
            # 3. Try alternative verification methods
    
    except Exception as e:
        logger.error(f"Error testing email verification: {str(e)}")
    
    finally:
        # Clean up resources
        email_verifier.cleanup()
        logger.info("Test completed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Instagram account creation with inbox.lv')
    parser.add_argument('--verify-only', action='store_true', help='Test only email verification')
    
    args = parser.parse_args()
    
    if args.verify_only:
        test_email_verification()
    else:
        test_account_creation_with_inbox_lv()