# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.bot_routes import bot_bp
    from app.routes.account_routes import account_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bot_bp)
    app.register_blueprint(account_bp)
    
    # Register Jinja filters
    @app.template_filter('status_color')
    def status_color(status):
        status_colors = {
            'pending': 'warning',
            'running': 'info',
            'completed': 'success',
            'failed': 'danger'
        }
        return status_colors.get(status, 'secondary')
    
    @app.template_filter('format_duration')
    def format_duration(seconds):
        if not seconds:
            return 'N/A'
            
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes} min {remaining_seconds} sec"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours} hr {minutes} min"
    
    return app