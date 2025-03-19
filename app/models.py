# app/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
 

class User(UserMixin, db.Model):
    """User model for application login"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    instagram_accounts = db.relationship('InstagramAccount', backref='owner', lazy='dynamic')
    task_history = db.relationship('TaskHistory', backref='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class InstagramAccount(db.Model):
    """Model for Instagram accounts managed by the system"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120))
    password_encrypted = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxy.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    verification_status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, failed
    verification_error = db.Column(db.Text, nullable=True)
    last_verified = db.Column(db.DateTime, nullable=True)
    # Account stats
    comment_count = db.Column(db.Integer, default=0)
    action_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<InstagramAccount {self.username}>'


class Proxy(db.Model):
    """Model for proxy servers used for Instagram automation"""
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(64), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    protocol = db.Column(db.String(10), default='http')
    username = db.Column(db.String(64))
    password_encrypted = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    failure_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    last_checked = db.Column(db.DateTime)
    country = db.Column(db.String(2))
    
    # Relationships
    instagram_accounts = db.relationship('InstagramAccount', backref='proxy', lazy='dynamic')
    
    def __repr__(self):
        return f'<Proxy {self.ip}:{self.port}>'


class TaskHistory(db.Model):
    """Model for tracking task execution history"""
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(64), nullable=False)  # 'account_creation', 'comment', etc.
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    result = db.Column(db.Text)
    error_message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<TaskHistory {self.task_type} {self.status}>'


class AccountCreationTask(db.Model):
    """Model for account creation tasks"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    email = db.Column(db.String(120))
    full_name = db.Column(db.String(100))
    use_temp_email = db.Column(db.Boolean, default=False)
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxy.id'))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    task_id = db.Column(db.String(64))  # Celery task ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<AccountCreationTask {self.username} {self.status}>'
import datetime

class BotTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    progress = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    target_url = db.Column(db.String(255), nullable=True)
    account_count = db.Column(db.Integer, default=0)
    action_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    result_data = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    celery_task_id = db.Column(db.String(50), nullable=True)
    
    # Relationship with User model
    user = db.relationship('User', backref=db.backref('bot_tasks', lazy=True))
    
    @property
    def eta(self):
        """Estimate time remaining based on progress and elapsed time"""
        if self.status == 'completed' or self.status == 'failed':
            return 0
            
        if self.progress <= 0:
            return None
            
        elapsed = datetime.datetime.utcnow() - self.created_at
        elapsed_seconds = elapsed.total_seconds()
        
        if elapsed_seconds <= 0:
            return None
            
        rate = self.progress / elapsed_seconds
        if rate <= 0:
            return None
            
        remaining_percent = 100 - self.progress
        eta_seconds = remaining_percent / rate
        
        return int(eta_seconds)
    
    @property
    def duration(self):
        """Calculate task duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))