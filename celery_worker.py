# celery_worker.py
from app import create_app
from app.celeryapp import create_celery_app
import os

# Windows-specific settings
if os.name == 'nt':
    # Set to prevent Celery from using forking on Windows
    os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

# Create Flask app
flask_app = create_app()

# Create Celery app with Flask context
celery = create_celery_app(flask_app)

# Import tasks to register them with Celery
import app.tasks