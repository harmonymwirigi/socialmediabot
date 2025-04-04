# app/utils/task_processor.py
import threading
import logging
import traceback
import datetime
import json
from app import db

logger = logging.getLogger(__name__)

def run_in_background(func):
    """Decorator to run a function in a background thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

@run_in_background
def process_comment_task(task_id, post_url, comments, account_ids=None, user_id=None):
    """Process comment task in a background thread"""
    from app.models import BotTask, InstagramAccount
    from app.services.instagram.account import InstagramAccountService
    from app.services.instagram.interaction import FixedInstagramInteractionService  # Ensure correct import path
    
    logger.info(f"Starting comment task for post: {post_url}")
    
    # Get Flask app context
    from app import create_app
    app = create_app()
    
    # Use app context for database operations
    with app.app_context():
        # Update task status to 'running'
        task = BotTask.query.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {'success': False, 'error': 'Task not found'}
        
        task.status = 'running'
        task.progress = 0
        db.session.commit()
        
        try:
            # Get accounts to use
            account_service = InstagramAccountService()
            
            if account_ids:
                # Get specific accounts - just usernames now
                accounts = []
                for account_id in account_ids:
                    account = InstagramAccount.query.get(account_id)
                    if account and account.is_active:
                        accounts.append(account.username)
            else:
                # Use all active accounts (just usernames)
                accounts = [username for username, _ in account_service.get_active_accounts()]
            
            if not accounts:
                logger.error("No active accounts found")
                task.status = 'failed'
                task.error_message = 'No active accounts found'
                task.completed_at = datetime.datetime.utcnow()
                
                db.session.commit()
                return {'success': False, 'error': 'No active accounts found'}
            
            # Setup progress callback
            def progress_callback(progress):
                logger.info(f"Comment progress: {progress}%")
                task.progress = int(progress)
                db.session.commit()
            
            # Create interaction service
            interaction_service = FixedInstagramInteractionService(account_service)
            interaction_service.set_progress_callback(progress_callback)
            
            # Start commenting process
            logger.info(f"Starting comment operation with {len(accounts)} accounts and {len(comments)} comments")
            results = interaction_service.comment_on_post(post_url, comments)
            
            # Calculate stats
            total_comments = len(comments)
            successful_comments = len([r for r in results if r['success']])
            success_rate = (successful_comments / total_comments) * 100 if total_comments > 0 else 0
            
            # Update task status
            task.status = 'completed'
            task.progress = 100
            task.completed_at = datetime.datetime.utcnow()
            task.result_data = json.dumps(results)
            task.success_rate = success_rate
            
            db.session.commit()
            
            logger.info(f"Comment task completed. Success rate: {success_rate:.2f}%")
            return {
                'success': True,
                'total_comments': total_comments,
                'successful_comments': successful_comments,
                'success_rate': success_rate,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Exception during comment task: {str(e)}")
            logger.error(traceback.format_exc())
            
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = datetime.datetime.utcnow()
            
            db.session.commit()
            return {'success': False, 'error': str(e)}
        


@run_in_background
def process_follow_task(task_id, profile_url, num_accounts, account_ids=None, user_id=None):
    """Process follow task in a background thread"""
    from app.models import BotTask, InstagramAccount
    from app.services.instagram.account import InstagramAccountService
    from app.services.instagram.interaction import FixedInstagramInteractionService
    
    logger.info(f"Starting follow task for profile: {profile_url}")
    
    # Get Flask app context
    from app import create_app
    app = create_app()
    
    # Use app context for database operations
    with app.app_context():
        # Update task status to 'running'
        task = BotTask.query.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {'success': False, 'error': 'Task not found'}
        
        task.status = 'running'
        task.progress = 0
        db.session.commit()
        
        try:
            # Get accounts to use
            account_service = InstagramAccountService()
            
            # Determine which accounts to use
            if account_ids:
                # Use specific accounts
                selected_accounts = []
                for account_id in account_ids:
                    account = InstagramAccount.query.get(account_id)
                    if account and account.is_active:
                        selected_accounts.append(account.username)
                        
                # Limit to requested number
                selected_accounts = selected_accounts[:num_accounts]
            else:
                # Use active accounts up to the requested number
                all_accounts = [username for username, _ in account_service.get_active_accounts()]
                selected_accounts = all_accounts[:num_accounts]
            
            actual_num_accounts = len(selected_accounts)
            
            if not selected_accounts:
                logger.error("No active accounts found")
                task.status = 'failed'
                task.error_message = 'No active accounts found'
                task.completed_at = datetime.datetime.utcnow()
                
                db.session.commit()
                return {'success': False, 'error': 'No active accounts found'}
            
            # Setup progress callback
            def progress_callback(progress):
                logger.info(f"Follow progress: {progress}%")
                task.progress = int(progress)
                db.session.commit()
            
            # Create interaction service
            interaction_service = FixedInstagramInteractionService(account_service)
            interaction_service.set_progress_callback(progress_callback)
            
            # Start follow operation
            logger.info(f"Starting follow operation with {actual_num_accounts} accounts")
            results = interaction_service.follow_profile(profile_url, actual_num_accounts)
            
            # Calculate stats
            successful_follows = len([r for r in results if r['success']])
            success_rate = (successful_follows / actual_num_accounts) * 100 if actual_num_accounts > 0 else 0

            # Update task status
            task.status = 'completed'
            task.progress = 100
            task.completed_at = datetime.datetime.utcnow()
            task.result_data = json.dumps(results)
            task.success_rate = success_rate
            task.action_count = successful_follows  # Ensure this is set correctly
            task.account_count = actual_num_accounts

            db.session.commit()

            # The section that updates account stats is likely not needed if we're updating it directly in _follow_with_account
            # But we'll keep it as a fallback
            for result in results:
                if result['success']:
                    try:
                        username = result['username']
                        account = InstagramAccount.query.filter_by(username=username).first()
                        if account:
                            account.action_count = account.action_count + 1 if account.action_count else 1
                            db.session.commit()
                    except Exception as e:
                        logger.error(f"Error updating account stats: {str(e)}")
            logger.info(f"Follow task completed. Success rate: {success_rate:.2f}%")
            return {
                'success': True,
                'total_accounts': actual_num_accounts,
                'successful_follows': successful_follows,
                'success_rate': success_rate,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Exception during follow task: {str(e)}")
            logger.error(traceback.format_exc())
            
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = datetime.datetime.utcnow()
            
            db.session.commit()
            return {'success': False, 'error': str(e)}