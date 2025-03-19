# test_celery.py
from celery import Celery

# Create Celery app with explicit Redis configuration
app = Celery('test_tasks', 
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

@app.task
def add(x, y):
    return x + y

if __name__ == '__main__':
    # This will only run when this file is executed directly
    app.start()