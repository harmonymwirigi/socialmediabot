# app/routes/bot_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import InstagramAccount, BotTask
from app import db
import datetime
import json

from app.utils.task_processor import process_comment_task
bot_bp = Blueprint('bot', __name__, url_prefix='/bot')
@bot_bp.route('/')
@login_required
def index():
    """Bot dashboard index"""
    # Get recent tasks
    recent_tasks = BotTask.query.filter_by(user_id=current_user.id).order_by(BotTask.created_at.desc()).limit(10).all()
    return render_template('bot/index.html', recent_tasks=recent_tasks)


@bot_bp.route('/comment', methods=['GET', 'POST'])
@login_required
def comment():
    """Comment bot interface"""
    if request.method == 'POST':
        post_url = request.form.get('post_url')
        comment_text = request.form.get('comment_text')
        selected_accounts = request.form.getlist('accounts')
        comment_count = int(request.form.get('comment_count', 1))
        
        if not post_url or not comment_text or not selected_accounts:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('bot.comment'))
        
        # Validate comment count
        if comment_count < 1:
            comment_count = 1
        elif comment_count > 100:
            comment_count = 100
        
        # Generate list of comments
        comments = []
        for _ in range(comment_count):
            comments.append(comment_text)
        
        # Create a task record
        task = BotTask(
            user_id=current_user.id,
            task_type='comment',
            status='pending',
            target_url=post_url,
            account_count=len(selected_accounts),
            action_count=len(comments),
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(task)
        db.session.commit()
        
        # Convert selected_accounts strings to integers
        account_ids = [int(account_id) for account_id in selected_accounts]
        
        # Use threading-based task processor
        thread = process_comment_task(
            task.id, post_url, comments, account_ids, current_user.id
        )
        
        # Set a dummy task ID
        task.celery_task_id = f"thread-{task.id}"
        db.session.commit()
        
        flash('Comment task created!', 'success')
        return redirect(url_for('bot.status', task_id=task.id))
    
    # GET request - show the form
    accounts = InstagramAccount.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('bot/comment.html', accounts=accounts)


@bot_bp.route('/tasks')
@login_required
def tasks():
    """View all bot tasks"""
    tasks = BotTask.query.filter_by(user_id=current_user.id).order_by(BotTask.created_at.desc()).all()
    return render_template('bot/tasks.html', tasks=tasks)

@bot_bp.route('/cancel/<int:task_id>', methods=['POST'])
@login_required
def cancel_task(task_id):
    """Cancel a pending task"""
    task = BotTask.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.user_id != current_user.id:
        flash('You do not have permission to cancel this task', 'danger')
        return redirect(url_for('bot.tasks'))
    
    # Only allow cancellation of pending tasks
    if task.status != 'pending':
        flash('Only pending tasks can be cancelled', 'warning')
        return redirect(url_for('bot.tasks'))
    
    # Update task status
    task.status = 'cancelled'
    task.completed_at = datetime.datetime.utcnow()
    db.session.commit()
    
    flash('Task has been cancelled', 'success')
    return redirect(url_for('bot.tasks'))

@bot_bp.route('/like', methods=['GET', 'POST'])
@login_required
def like():
    """Like Instagram posts"""
    # Get all active accounts for the form
    accounts = InstagramAccount.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Get form data
        post_url = request.form.get('post_url', '').strip()
        hashtag = request.form.get('hashtag', '').strip()
        post_count = int(request.form.get('post_count', 10))
        account_ids = request.form.getlist('accounts')
        min_delay = int(request.form.get('min_delay', 3))
        max_delay = int(request.form.get('max_delay', 8))
        
        # Validate input
        if (not post_url and not hashtag) or not account_ids:
            flash('Please enter a post URL or hashtag and select at least one account', 'danger')
            return redirect(url_for('bot.like'))
        
        # Create task based on type
        if post_url:
            # Clean up URL if needed
            if not post_url.startswith(('http://', 'https://')):
                post_url = 'https://www.instagram.com/p/' + post_url.strip('/')
                if not post_url.endswith('/'):
                    post_url += '/'
            
            # Create task record for liking a single post
            task = BotTask(
                user_id=current_user.id,
                task_type='like_post',
                status='pending',
                target_url=post_url,
                account_count=len(account_ids),
                action_count=0
            )
            db.session.add(task)
            db.session.commit()
            
            # Start background task for liking a post
            from app.utils.task_processor import process_like_task
            process_like_task(
                task_id=task.id,
                post_url=post_url,
                num_accounts=len(account_ids),
                account_ids=account_ids,
                user_id=current_user.id
            )
            
            flash(f'Like task for post has been started with {len(account_ids)} accounts', 'success')
            
        elif hashtag:
            # TODO: Implement hashtag-based liking in the future
            flash('Liking by hashtag is not yet implemented', 'warning')
            return redirect(url_for('bot.like'))
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('bot/like.html', accounts=accounts)

@bot_bp.route('/follow', methods=['GET', 'POST'])
@login_required
def follow():
    """Follow Instagram profiles"""
    # Get all active accounts for the form
    accounts = InstagramAccount.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Get form data
        profile_url = request.form.get('profile_url', '').strip()
        num_accounts = int(request.form.get('num_accounts', 1))
        account_ids = request.form.getlist('accounts')
        min_delay = int(request.form.get('min_delay', 5))
        max_delay = int(request.form.get('max_delay', 10))
        
        # Validate input
        if not profile_url:
            flash('Please enter a profile URL', 'danger')
            return redirect(url_for('bot.follow'))
        
        # Clean up URL if needed
        if not profile_url.startswith(('http://', 'https://')):
            profile_url = 'https://www.instagram.com/' + profile_url.lstrip('@')
            if not profile_url.endswith('/'):
                profile_url += '/'
        
        # Ensure we have accounts selected
        if not account_ids:
            flash('Please select at least one account', 'danger')
            return redirect(url_for('bot.follow'))
        
        # Create task record
        task = BotTask(
            user_id=current_user.id,
            task_type='follow',
            status='pending',
            target_url=profile_url,
            account_count=len(account_ids),
            action_count=0
        )
        db.session.add(task)
        db.session.commit()
        
        # Start background task
        from app.utils.task_processor import process_follow_task
        process_follow_task(
            task_id=task.id,
            profile_url=profile_url,
            num_accounts=num_accounts,
            account_ids=account_ids,
            user_id=current_user.id
        )
        
        flash('Follow task has been started', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('bot/follow.html', accounts=accounts)

@bot_bp.route('/status/<int:task_id>')
@login_required
def status(task_id):
    """View status of a bot task"""
    task = BotTask.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.user_id != current_user.id:
        flash('You do not have permission to view this task', 'danger')
        return redirect(url_for('bot.tasks'))
    
    return render_template('bot/status.html', task=task)


@bot_bp.route('/api/status/<int:task_id>')
@login_required
def api_status(task_id):
    """API endpoint for bot task status"""
    task = BotTask.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Format the result data if available
    result_data = None
    if task.result_data:
        try:
            result_data = json.loads(task.result_data)
        except:
            result_data = None
    
    status_data = {
        'id': task.id,
        'status': task.status,
        'progress': task.progress,
        'task_type': task.task_type,
        'target_url': task.target_url,
        'created_at': task.created_at.isoformat(),
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'account_count': task.account_count,
        'action_count': task.action_count,
        'success_rate': task.success_rate,
        'error_message': task.error_message,
        'result_data': result_data,
        'eta': task.eta
    }
    
    return jsonify(status_data)
from app.tasks.bot_tasks import comment_on_post_task