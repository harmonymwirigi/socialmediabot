# app/routes/main_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from app.models import InstagramAccount, TaskHistory
from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for authenticated users"""
    # Get stats for the dashboard
    account_count = InstagramAccount.query.filter_by(user_id=current_user.id).count()
    active_accounts = InstagramAccount.query.filter_by(user_id=current_user.id, is_active=True).count()
    
    # Get recent tasks
    recent_tasks = TaskHistory.query.filter_by(user_id=current_user.id) \
        .order_by(TaskHistory.start_time.desc()).limit(5).all()
    
    # Get recent comments (placeholder)
    recent_actions = []
    
    return render_template('dashboard.html', 
                          account_count=account_count,
                          active_accounts=active_accounts,
                          recent_tasks=recent_tasks,
                          recent_actions=recent_actions)


@main_bp.route('/logs')
@login_required
def view_logs():
    """View application logs"""
    # This is a simplified version - in production, you'd want pagination and filtering
    try:
        with open(current_app.config['LOG_FILE'], 'r') as f:
            logs = f.readlines()
            # Get only the last 100 lines
            logs = logs[-100:]
    except FileNotFoundError:
        logs = ["No log file found."]
    except Exception as e:
        logs = [f"Error reading log file: {str(e)}"]
    
    return render_template('logs.html', logs=logs)


@main_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('settings.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@main_bp.errorhandler(404)
def page_not_found(e):
    """Custom 404 page"""
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def server_error(e):
    """Custom 500 page"""
    return render_template('500.html'), 500