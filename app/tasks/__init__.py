# app/tasks/__init__.py
# Import tasks to register them with Celery
from app.tasks.bot_tasks import comment_on_post_task