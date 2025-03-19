# app/routes/account_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import InstagramAccount, Proxy, AccountCreationTask
from app import db
from app.services.utils.proxy_manager import ProxyManager
from app.services.utils.email_verifier import EmailVerifier
import time
import random
import string
import datetime
import logging
import os
from cryptography.fernet import Fernet

# Create a logger
logger = logging.getLogger(__name__)

# Encryption key for passwords (in a real app, this should be securely stored)
# This is just for demonstration purposes
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

account_bp = Blueprint('accounts', __name__, url_prefix='/accounts')

# List all Instagram accounts
@account_bp.route('/')
@login_required
def account_list():
    """List all Instagram accounts"""
    accounts = InstagramAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts/list.html', accounts=accounts)

# Create a new Instagram account
@account_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_account():
    """Instagram account creation page"""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        fullname = request.form.get('fullname')
        password = request.form.get('password')
        use_temp_email = 'temp_email' in request.form
        use_proxy = 'use_proxy' in request.form
        proxy_id = request.form.get('proxy_id') if use_proxy else None
        
        # Validate inputs
        if not username or not fullname:
            flash('Username and full name are required', 'danger')
            return redirect(url_for('accounts.create_account'))
        
        if not use_temp_email and not email:
            flash('Email is required when not using temporary email', 'danger')
            return redirect(url_for('accounts.create_account'))
        
        if not password:
            # Generate a random password if none provided
            password = ''.join(random.choice(string.ascii_letters + string.digits + '!@#$%^&*()') for _ in range(12))
        
        # Create a new account creation task
        task = AccountCreationTask(
            username=username,
            email=email,
            full_name=fullname,
            use_temp_email=use_temp_email,
            proxy_id=proxy_id,
            status='pending',
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        
        # For now, just simulate task processing
        # In a real app, this would be done in a Celery task
        task.status = 'running'
        db.session.commit()
        
        # Simulate processing time (would be done by Celery in production)
        # This is just for demonstration - in real app this would be blocking
        # and should be done in a background task
        success = random.choice([True, False])
        
        if success:
            # Simulate successful account creation
            encrypted_password = fernet.encrypt(password.encode()).decode()
            new_account = InstagramAccount(
                username=username,
                email=email,
                password_encrypted=encrypted_password,
                full_name=fullname,
                is_active=True,
                creation_date=datetime.datetime.utcnow(),
                user_id=current_user.id,
                proxy_id=proxy_id if proxy_id else None
            )
            db.session.add(new_account)
            
            task.status = 'completed'
            task.completed_at = datetime.datetime.utcnow()
        else:
            # Simulate failed account creation
            task.status = 'failed'
            task.completed_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        flash('Account creation task started!', 'success')
        return redirect(url_for('accounts.creation_status', task_id=task.id))
    
    # GET request - show the form
    proxies = Proxy.query.filter_by(is_active=True).all()
    return render_template('accounts/create.html', proxies=proxies)

# Add existing Instagram account
@account_bp.route('/add-existing', methods=['GET', 'POST'])
@login_required
def add_existing():
    """Add an existing Instagram account"""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        proxy_id = request.form.get('proxy_id')
        verify_now = 'verify_now' in request.form
        
        # Validate inputs
        if not username or not password:
            flash('Username and password are required', 'danger')
            return redirect(url_for('accounts.add_existing'))
        
        # Check if account already exists for this user
        existing_account = InstagramAccount.query.filter_by(
            username=username,
            user_id=current_user.id
        ).first()
        
        if existing_account:
            flash(f'An account with username {username} already exists', 'warning')
            return redirect(url_for('accounts.account_list'))
        
        # Generate a fresh encryption key
        from cryptography.fernet import Fernet
        key_path = 'secret.key'
        if not os.path.exists(key_path):
            key = Fernet.generate_key()
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
        else:
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
                
        # Create Fernet instance with key and encrypt password
        fernet = Fernet(key)
        encrypted_password = fernet.encrypt(password.encode())
        
        # Create a new account
        new_account = InstagramAccount(
            username=username,
            email=email,
            password_encrypted=encrypted_password,
            full_name=username,  # Use username as fallback for full name
            is_active=True,
            is_verified=False,
            verification_status='pending',
            creation_date=datetime.datetime.utcnow(),
            user_id=current_user.id,
            proxy_id=proxy_id if proxy_id else None
        )
        
        db.session.add(new_account)
        db.session.commit()
        
        # Verify the account if requested
        if verify_now:
            from app.services.instagram.account_verification import verify_instagram_account
            verify_instagram_account(new_account.id)
            
            flash(f'Account {username} added! Verification started in background.', 'info')
            return redirect(url_for('accounts.account_status', account_id=new_account.id))
        else:
            flash(f'Account {username} added successfully! (Not verified)', 'success')
            return redirect(url_for('accounts.account_list'))
    
    # GET request - show the form
    proxies = Proxy.query.filter_by(is_active=True).all()
    return render_template('accounts/add_existing.html', proxies=proxies)

# Verify an account

@account_bp.route('/verify/<int:account_id>', methods=['POST'])
@login_required
def verify_account(account_id):
    """Manually trigger account verification"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to modify this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    # Reset verification status
    account.verification_status = 'pending' 
    account.verification_error = None
    db.session.commit()
    
    # Import account verification service
    from app.services.instagram.account_verification import verify_instagram_account
    
    # Start verification in background
    verify_instagram_account(account.id)
    
    flash(f'Verification started for account {account.username}', 'info')
    return redirect(url_for('accounts.account_status', account_id=account.id))

@account_bp.route('/reset-password/<int:account_id>', methods=['GET', 'POST'])
@login_required
def reset_account_password(account_id):
    """Reset the password for an account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to modify this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        
        if not new_password:
            flash('Password is required', 'danger')
            return redirect(url_for('accounts.reset_account_password', account_id=account_id))
        
        # Update the password with new encryption
        from app.utils.encryption import get_encryption_key
        key = get_encryption_key()
        fernet = Fernet(key)
        
        # Encrypt the new password
        encrypted_password = fernet.encrypt(new_password.encode())
        
        # Update account
        account.password_encrypted = encrypted_password
        account.is_verified = False
        account.verification_status = 'pending'
        account.verification_error = None
        db.session.commit()
        
        flash('Password updated successfully!', 'success')
        return redirect(url_for('accounts.account_status', account_id=account_id))
    
    return render_template('accounts/reset_password.html', account=account)
@account_bp.route('/status/<int:task_id>')
@login_required
def creation_status(task_id):
    """View status of an account creation task"""
    task = AccountCreationTask.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.user_id != current_user.id:
        flash('You do not have permission to view this task', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    return render_template('accounts/status.html', task=task)
# Add these routes to your existing account_routes.py file

@account_bp.route('/manual-verify/<int:account_id>', methods=['GET', 'POST'])
@login_required
def manual_verify_account(account_id):
    """Start manual verification process for an account requiring 2FA/verification"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to modify this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    if request.method == 'POST':
        # Start manual verification process
        from app.services.instagram.account_verification import manual_verification_monitor
        
        # Start the manual verification process
        result = manual_verification_monitor(account_id)
        
        if result['status'] == 'initiated':
            flash(f'Manual verification started for {account.username}. Please complete the login in the opened browser window.', 'info')
            return redirect(url_for('accounts.manual_verify_status', account_id=account_id))
        else:
            flash(f'Error starting manual verification: {result.get("message", "Unknown error")}', 'danger')
            return redirect(url_for('accounts.account_list'))
    
    # GET request - show the confirmation page
    return render_template('accounts/manual_verify.html', account=account)

@account_bp.route('/manual-verify-status/<int:account_id>')
@login_required
def manual_verify_status(account_id):
    """Show status page for manual verification"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to view this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    return render_template('accounts/manual_verify_status.html', account=account)

@account_bp.route('/api/manual-verify-status/<int:account_id>')
@login_required
def api_manual_verify_status(account_id):
    """API endpoint to check manual verification status"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    status = account.verification_status
    is_verified = account.is_verified
    error = account.verification_error
    
    response = {
        'id': account.id,
        'username': account.username,
        'status': status,
        'is_verified': is_verified,
        'error': error,
        'last_verified': account.last_verified.isoformat() if account.last_verified else None
    }
    
    return jsonify(response)

# Add these routes to your existing account_routes.py file

@account_bp.route('/manual-login/<int:account_id>', methods=['GET', 'POST'])
@login_required
def manual_login_account(account_id):
    """Start manual login process for an Instagram account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to modify this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    if request.method == 'POST':
        # Start manual verification process
        from app.services.instagram.account_verification import manual_verification_monitor
        
        # Start the manual verification process
        result = manual_verification_monitor(account_id)
        
        if result['status'] == 'initiated':
            flash(f'Manual login started for {account.username}. Please complete the login in the opened browser window.', 'info')
            return redirect(url_for('accounts.manual_login_status', account_id=account_id))
        else:
            flash(f'Error starting manual login: {result.get("message", "Unknown error")}', 'danger')
            return redirect(url_for('accounts.account_list'))
    
    # GET request - show the confirmation page
    return render_template('accounts/manual_verify.html', account=account)

@account_bp.route('/manual-login-status/<int:account_id>')
@login_required
def manual_login_status(account_id):
    """Show status page for manual login"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to view this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    return render_template('accounts/manual_verify_status.html', account=account)

@account_bp.route('/api/manual-login-status/<int:account_id>')
@login_required
def api_manual_login_status(account_id):
    """API endpoint to check manual login status"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    status = account.verification_status
    is_verified = account.is_verified
    error = account.verification_error
    
    response = {
        'id': account.id,
        'username': account.username,
        'status': status,
        'is_verified': is_verified,
        'error': error,
        'last_verified': account.last_verified.isoformat() if account.last_verified else None
    }
    
    return jsonify(response)
@account_bp.route('/api/status/<int:task_id>')
@login_required
def api_creation_status(task_id):
    """API endpoint to check account creation status"""
    task = AccountCreationTask.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get task logs (mock data for now)
    task_logs = [
        f"{time.strftime('%H:%M:%S')} - Starting account creation for {task.username}",
        f"{time.strftime('%H:%M:%S')} - Setting up browser...",
        f"{time.strftime('%H:%M:%S')} - Navigating to Instagram..."
    ]
    
    response = {
        'id': task.id,
        'username': task.username,
        'status': task.status,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'logs': task_logs
    }
    
    return jsonify(response)

@account_bp.route('/check-username')
@login_required
def check_username():
    """Check if a username is available on Instagram"""
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    # For demo, randomly determine if username is available
    is_available = random.choice([True, False])
    
    return jsonify({
        'username': username,
        'available': is_available
    })
@account_bp.route('/status/<int:account_id>')
@login_required
def account_status(account_id):
    """View verification status of an account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to view this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    return render_template('accounts/status.html', account=account)
@account_bp.route('/<int:account_id>')
@login_required
def account_detail(account_id):
    """View details of a specific Instagram account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to view this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    return render_template('accounts/detail.html', account=account)

@account_bp.route('/<int:account_id>/deactivate', methods=['POST'])
@login_required
def deactivate_account(account_id):
    """Deactivate an Instagram account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to modify this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    account.is_active = False
    db.session.commit()
    
    flash(f'Account {account.username} has been deactivated', 'success')
    return redirect(url_for('accounts.account_list'))

@account_bp.route('/<int:account_id>/activate', methods=['POST'])
@login_required
def activate_account(account_id):
    """Activate an Instagram account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to modify this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    account.is_active = True
    db.session.commit()
    
    flash(f'Account {account.username} has been activated', 'success')
    return redirect(url_for('accounts.account_list'))

@account_bp.route('/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_account(account_id):
    """Delete an Instagram account"""
    account = InstagramAccount.query.get_or_404(account_id)
    
    # Ensure the account belongs to the current user
    if account.user_id != current_user.id:
        flash('You do not have permission to delete this account', 'danger')
        return redirect(url_for('accounts.account_list'))
    
    username = account.username
    db.session.delete(account)
    db.session.commit()
    
    flash(f'Account {username} has been deleted', 'success')
    return redirect(url_for('accounts.account_list'))