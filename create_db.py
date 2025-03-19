# create_db.py
from app import create_app, db
from app.models import User, InstagramAccount, Proxy, TaskHistory, AccountCreationTask, BotTask

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully")
    
    # List all tables to verify
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables in database:")
    for table in tables:
        print(f"- {table}")