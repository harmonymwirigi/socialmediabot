# app/celeryapp.py
from celery import Celery

def create_celery_app(app=None):
    """
    Create a Celery app instance
    """
    celery = Celery(
        'social_media_bot',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )

    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            if app:
                with app.app_context():
                    return self.run(*args, **kwargs)
            return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Create a celery instance without Flask context for task registration
celery = create_celery_app()