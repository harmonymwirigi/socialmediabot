# app/services/instagram/account_verification.py
import logging
import traceback
import datetime
import time
from app import db
from app.models import InstagramAccount
from app.utils.task_processor import run_in_background

logger = logging.getLogger(__name__)

@run_in_background
def verify_instagram_account(account_id, verification_callback=None, manual_mode=True):
    """
    Verify Instagram account by opening a browser for manual login
    
    Args:
        account_id: ID of the InstagramAccount to verify
        verification_callback: Optional callback function to call with results
        manual_mode: If True (default), opens browser for manual login
    """
    # Get Flask app context
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Get the account
        account = InstagramAccount.query.get(account_id)
        if not account:
            logger.error(f"Account ID {account_id} not found")
            if verification_callback:
                verification_callback(False, "Account not found")
            return False
        
        try:
            logger.info(f"Starting verification for account: {account.username}")
            account.verification_status = 'in_progress'
            db.session.commit()
            
            # Create browser instance
            from app.services.instagram.browser import InstagramBrowser
            browser = InstagramBrowser()
            
            # Start manual login process
            logger.info(f"Starting manual login for account: {account.username}")
            success = browser.initiate_manual_login(account.username)
            
            if success:
                logger.info(f"Manual login successful for: {account.username}")
                
                # Update account
                account.is_verified = True
                account.last_verified = datetime.datetime.utcnow()
                account.verification_status = 'completed'
                account.verification_error = None
                db.session.commit()
                
                if verification_callback:
                    verification_callback(True, "Account verified successfully via manual login")
                
                return True
            else:
                logger.warning(f"Manual login failed for: {account.username}")
                
                # Update account
                account.is_verified = False
                account.verification_status = 'failed'
                account.verification_error = "Manual login failed or abandoned"
                db.session.commit()
                
                if verification_callback:
                    verification_callback(False, "Manual login failed")
                
                return False
                
        except Exception as e:
            logger.error(f"Error verifying account {account.username}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update account
            account.is_verified = False
            account.verification_status = 'failed'
            account.verification_error = str(e)
            db.session.commit()
            
            if verification_callback:
                verification_callback(False, str(e))
            
            return False


def manual_verification_monitor(account_id, timeout=300):
    """
    Monitor manual verification progress with timeout
    
    Args:
        account_id: ID of the InstagramAccount being verified
        timeout: Maximum time in seconds to wait for manual verification
    
    Returns:
        dict: Status information about the verification process
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        start_time = time.time()
        account = InstagramAccount.query.get(account_id)
        
        if not account:
            return {"status": "error", "message": "Account not found"}
        
        # Update account status
        account.verification_status = 'manual_verification'
        db.session.commit()
        
        # Start manual verification in background
        verify_instagram_account(account_id)
        
        # Return immediately so frontend can monitor status
        return {
            "status": "initiated",
            "account_id": account_id,
            "username": account.username,
            "start_time": start_time,
            "timeout": timeout
        }