"""
Database Migration to Remove Password Encryption

This script will update your database schema to remove the password_encrypted field
from the InstagramAccount table. It will preserve all other data.

IMPORTANT: Make a backup of your database before running this script!
"""

import sys
import os
from datetime import datetime

# Add parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from app import create_app, db
from sqlalchemy import text, inspect

def run_migration():
    """Run the migration to remove password_encrypted field"""
    
    print("Starting migration process...")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        try:
            # Check if the column exists
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('instagram_account')]
            
            if 'password_encrypted' in columns:
                print("Found password_encrypted column, proceeding with migration...")
                
                # Create a backup of the table data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_table = f"instagram_account_backup_{timestamp}"
                
                print(f"Creating backup table: {backup_table}")
                
                # Use session for SQLAlchemy operations
                with db.engine.connect() as conn:
                    # Create backup table
                    conn.execute(text(f"CREATE TABLE {backup_table} LIKE instagram_account"))
                    conn.execute(text(f"INSERT INTO {backup_table} SELECT * FROM instagram_account"))
                    
                    # Get the number of rows
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {backup_table}"))
                    row_count = result.scalar()
                    print(f"Backed up {row_count} rows to {backup_table}")
                    
                    # MySQL supports dropping columns directly
                    print("Dropping password_encrypted column...")
                    conn.execute(text("ALTER TABLE instagram_account DROP COLUMN password_encrypted"))
                    
                    # Commit the transaction
                    conn.commit()
                    
                print("Migration completed successfully!")
                print(f"A backup of your data is available in the {backup_table} table")
                
            else:
                print("The password_encrypted column does not exist, no migration needed")
                
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            
if __name__ == "__main__":
    # Ask for confirmation
    print("WARNING: This script will modify your database schema.")
    print("Make sure you have a backup of your database before proceeding.")
    
    confirm = input("Do you want to continue? (yes/no): ")
    if confirm.lower() != "yes":
        print("Migration cancelled")
        sys.exit(0)
        
    run_migration()