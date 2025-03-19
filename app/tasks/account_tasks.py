# app/tasks/account_tasks.py
from celery import Celery
from flask import current_app
import os
import time
import logging
import traceback
from app import create_app, db
from app.models import AccountCreationTask, InstagramAccount, Proxy, TaskHistory
from app.services.instagram.account_creator import InstagramAccountCreator
from app.services.utils.proxy_manager import ProxyManager
from app.services.utils.email_verifier import EmailVerifier
from app.services.utils.captcha_solver import CaptchaSolver
from cryptography.fernet import Fernet
import datetime

# Create celery instance
celery = Celery('tasks')

# Configure Celery
def configure_celery(app):
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# Setup logging
def setup_task_logging(task_id):
    log_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_folder, exist_ok=True)
    
    log_file = os.path.join(log_folder, f'task_{task_id}.log')
    
    # Configure file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Get logger and add handler
    logger = logging.getLogger(f'task_{task_id}')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    return logger
# app/tasks/account_tasks.py - Add this function

@celery.task
def verify_instagram_account(account_id):
    """Verify Instagram account by attempting login and saving cookies"""
    app = create_app()
    
    with app.app_context():
        # Get the account
        account = InstagramAccount.query.get(account_id)
        if not account:
            return {'success': False, 'error': 'Account not found'}
        
        # Set up logging
        logger = logging.getLogger(f'account_verification_{account_id}')
        
        try:
            # Get decrypted password
            from cryptography.fernet import Fernet
            with open('secret.key', 'rb') as key_file:
                key = key_file.read()
            fernet = Fernet(key)
            
            # Handle string vs bytes for encrypted password
            encrypted_password = account.password_encrypted
            if isinstance(encrypted_password, str):
                try:
                    import base64
                    encrypted_password = base64.b64decode(encrypted_password)
                except:
                    encrypted_password = encrypted_password.encode()
            
            password = fernet.decrypt(encrypted_password).decode()
            
            # Create browser instance
            from app.services.instagram.browser import InstagramBrowser
            browser = InstagramBrowser()
            
            # Attempt login
            logger.info(f"Attempting verification login for account: {account.username}")
            driver = browser.login(account.username, password)
            
            if driver:
                # Login successful, update account
                account.is_verified = True
                account.last_verified = datetime.datetime.utcnow()
                db.session.commit()
                
                # Clean up driver
                driver.quit()
                
                logger.info(f"Account verification successful: {account.username}")
                return {'success': True, 'message': 'Account verified successfully'}
            else:
                # Login failed
                account.is_verified = False
                db.session.commit()
                
                logger.warning(f"Account verification failed: {account.username}")
                return {'success': False, 'error': 'Login verification failed'}
                
        except Exception as e:
            # Handle errors
            logger.error(f"Error during account verification: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update account status
            account.is_verified = False
            db.session.commit()
            
            return {'success': False, 'error': str(e)}
@celery.task
def create_instagram_account(task_id, username, email, fullname, password, 
                            use_temp_email=False, proxy_id=None, user_id=None):
    """
    Celery task to create an Instagram account
    """
    app = create_app()
    configure_celery(app)
    
    with app.app_context():
        # Setup task logging
        logger = setup_task_logging(task_id)
        logger.info(f"Starting account creation task for {username}")
        
        # Update task status to 'running'
        task = AccountCreationTask.query.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {'success': False, 'error': 'Task not found'}
        
        task.status = 'running'
        db.session.commit()
        
        # Create history record
        history = TaskHistory(
            task_type='account_creation',
            status='running',
            user_id=user_id,
            start_time=datetime.datetime.utcnow()
        )
        db.session.add(history)
        db.session.commit()
        
        try:
            # Setup services
            proxy_manager = ProxyManager()
            email_verifier = EmailVerifier()
            captcha_solver = CaptchaSolver()
            
            # If use_temp_email is True, generate a temporary email
            if use_temp_email:
                generated_email = email_verifier.generate_temp_email()
                if not generated_email:
                    logger.error("Failed to generate temporary email")
                    task.status = 'failed'
                    task.completed_at = datetime.datetime.utcnow()
                    history.status = 'failed'
                    history.end_time = datetime.datetime.utcnow()
                    history.error_message = "Failed to generate temporary email"
                    db.session.commit()
                    return {'success': False, 'error': 'Failed to generate temporary email'}
                
                logger.info(f"Generated temporary email: {generated_email}")
                email = generated_email
                task.email = email
                db.session.commit()
            
            # If proxy_id is provided, get the proxy
            proxy = None
            if proxy_id:
                proxy = Proxy.query.get(proxy_id)
                if proxy:
                    logger.info(f"Using proxy: {proxy.ip}:{proxy.port}")
                    proxy_dict = {
                        'ip': proxy.ip,
                        'port': proxy.port,
                        'protocol': proxy.protocol,
                        'username': proxy.username,
                        'password': proxy.password_encrypted  # Note: This needs decryption
                    }
                    proxy_manager.add_proxies([proxy_dict])
            
            # Setup account creator with progress callback
            class ProgressCallback:
                def __init__(self, task_id):
                    self.task_id = task_id
                
                def update_progress(self, progress):
                    logger.info(f"Progress: {progress}%")
            
            progress_callback = ProgressCallback(task_id)
            
            # Create a mock account service for now
            class MockAccountService:
                def __init__(self):
                    # Create encryption key - in production, this should be stored securely
                    self.key = Fernet.generate_key()
                    self.fernet = Fernet(self.key)
                
                def add_account(self, username, password):
                    encrypted_password = self.fernet.encrypt(password.encode()).decode()
                    new_account = InstagramAccount(
                        username=username,
                        password_encrypted=encrypted_password,
                        email=email,
                        full_name=fullname,
                        is_active=True,
                        creation_date=datetime.datetime.utcnow(),
                        user_id=user_id,
                        proxy_id=proxy_id if proxy_id else None
                    )
                    db.session.add(new_account)
                    db.session.commit()
                    logger.info(f"Added account {username} to database")
                    return True
            
            account_service = MockAccountService()
            
            account_creator = InstagramAccountCreator(
                account_service=account_service,
                proxy_manager=proxy_manager,
                email_verifier=email_verifier,
                captcha_solver=captcha_solver
            )
            
            # Set the progress callback
            account_creator.set_callbacks(progress_callback=progress_callback.update_progress)
            
            # Prepare the date of birth
            # Use a random adult age between 18-40 years
            import random
            from datetime import datetime, timedelta
            min_age = 18
            max_age = 40
            days_in_year = 365.25
            
            max_birth_date = datetime.now() - timedelta(days=min_age * days_in_year)
            min_birth_date = datetime.now() - timedelta(days=max_age * days_in_year)
            
            random_days = random.randint(0, int((max_birth_date - min_birth_date).days))
            birth_date = min_birth_date + timedelta(days=random_days)
            
            date_of_birth = (birth_date.month, birth_date.day, birth_date.year)
            
            # Perform the account creation
            logger.info(f"Starting Instagram account creation for {username}")
            
            result = account_creator.create_account(
                email=email,
                fullname=fullname,
                username=username,
                password=password,
                phone=None,  # Optional phone number
                date_of_birth=date_of_birth,
                gender=random.choice(['Male', 'Female']),
                profile_pic=None,  # Optional profile picture path
                bio=None  # Optional biography
            )
            
            # Update task based on result
            if result['success']:
                logger.info(f"Successfully created Instagram account: {username}")
                task.status = 'completed'
                task.completed_at = datetime.datetime.utcnow()
                
                history.status = 'completed'
                history.end_time = datetime.datetime.utcnow()
                history.result = f"Successfully created Instagram account: {username}"
                
                db.session.commit()
                return {
                    'success': True, 
                    'username': username,
                    'email': email,
                    'message': 'Account created successfully'
                }
            else:
                logger.error(f"Failed to create Instagram account: {result.get('error', 'Unknown error')}")
                
                task.status = 'failed'
                task.completed_at = datetime.datetime.utcnow()
                
                history.status = 'failed'
                history.end_time = datetime.datetime.utcnow()
                history.error_message = result.get('error', 'Unknown error')
                
                db.session.commit()
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'verification_required': result.get('verification_required', False),
                    'verification_type': result.get('verification_type', None)
                }
                
        except Exception as e:
            logger.error(f"Exception during account creation: {str(e)}")
            logger.error(traceback.format_exc())
            
            task.status = 'failed'
            task.completed_at = datetime.datetime.utcnow()
            
            history.status = 'failed'
            history.end_time = datetime.datetime.utcnow()
            history.error_message = str(e)
            
            db.session.commit()
            return {'success': False, 'error': str(e)}


@celery.task
def check_account_status(account_id):
    """
    Check the status of an Instagram account
    """
    app = create_app()
    configure_celery(app)
    
    with app.app_context():
        try:
            # Get the account
            account = InstagramAccount.query.get(account_id)
            if not account:
                return {'success': False, 'error': 'Account not found'}
            
            # Create a browser instance
            from app.services.instagram.browser import InstagramBrowser
            browser = InstagramBrowser()
            
            # Check if cookies exist
            if browser._check_cookies_exist(account.username):
                # Try to create a session
                driver = browser.create_comment_session(account.username, "https://www.instagram.com/")
                if driver:
                    # Check if login is successful
                    is_logged_in = browser._verify_login(driver)
                    driver.quit()
                    
                    # Update account status
                    account.is_active = is_logged_in
                    account.last_used = datetime.datetime.utcnow()
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'account_id': account_id,
                        'username': account.username,
                        'is_active': is_logged_in
                    }
            
            # If no cookies or session creation failed
            account.is_active = False
            db.session.commit()
            
            return {
                'success': False,
                'account_id': account_id,
                'username': account.username,
                'is_active': False,
                'error': 'Failed to verify account status'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}