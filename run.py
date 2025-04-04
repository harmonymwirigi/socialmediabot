# run.py
from app import create_app, db
from flask import render_template
import datetime
from sqlalchemy import text

app = create_app()

# Use with_app_context instead of before_first_request
def verify_db_connection():
    """Verify database connection and print info to console"""
    try:
        # Check connection by executing a simple query
        result = db.session.execute(text('SELECT DATABASE() as db_name, @@version as version'))
        info = result.fetchone()
        
        # Print connection information
        print("\n" + "="*50)
        print("DATABASE CONNECTION VERIFIED")
        print("="*50)
        print(f"Connected to database: {info.db_name}")
        print(f"MySQL version: {info.version}")
        
        # Get table count
        result = db.session.execute(text(
            "SELECT COUNT(*) as table_count FROM information_schema.tables "
            "WHERE table_schema = :schema"), 
            {"schema": info.db_name})
        table_count = result.fetchone().table_count
        print(f"Number of tables: {table_count}")
        
        if table_count == 0:
            print("No tables found. Creating database tables...")
            db.create_all()  # Create tables based on your models
            print("Tables created successfully.")
        else:
            print("Existing tables found in database.")
        
        print("="*50 + "\n")
    except Exception as e:
        print("\n" + "="*50)
        print("DATABASE CONNECTION ERROR")
        print("="*50)
        print(f"Error: {str(e)}")
        print("Please ensure:")
        print("1. SSH tunnel is running in Git Bash")
        print("2. Database credentials are correct")
        print("3. PythonAnywhere MySQL server is running")
        print("="*50 + "\n")
        raise e  # Re-raise to stop app if connection fails

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        verify_db_connection()  # Run verification before starting the app
    app.run(debug=True)