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
    """Like bot interface"""
    if request.method == 'POST':
        post_url = request.form.get('post_url')
        selected_accounts = request.form.getlist('accounts')
        
        if not post_url or not selected_accounts:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('bot.like'))
        
        # Create a task for liking
        flash('Like task created!', 'success')
        return redirect(url_for('bot.like'))
    
    # GET request - show the form
    accounts = InstagramAccount.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('bot/like.html', accounts=accounts)

@bot_bp.route('/follow', methods=['GET', 'POST'])
@login_required
def follow():
    """Follow bot interface"""
    if request.method == 'POST':
        username = request.form.get('username')
        selected_accounts = request.form.getlist('accounts')
        
        if not username or not selected_accounts:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('bot.follow'))
        
        # Create a task for following
        flash('Follow task created!', 'success')
        return redirect(url_for('bot.follow'))
    
    # GET request - show the form
    accounts = InstagramAccount.query.filter_by(user_id=current_user.id, is_active=True).all()
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