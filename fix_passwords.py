# fix_passwords.py
from app import create_app, db
from app.models import InstagramAccount
from cryptography.fernet import Fernet
import os

# Create Flask app context
app = create_app()

with app.app_context():
    # Check if we have accounts
    accounts = InstagramAccount.query.all()
    print(f"Found {len(accounts)} accounts in database")
    
    for account in accounts:
        print(f"Account: {account.username}")
        
        # Get encrypted password data
        encrypted_password = account.password_encrypted
        
        # Check if it's bytes or string
        if isinstance(encrypted_password, str):
            print("  - Password is stored as string, should be bytes")
            try:
                # Try to convert to bytes if it's base64-encoded
                import base64
                encrypted_bytes = base64.b64decode(encrypted_password)
                print("  - Converted to bytes successfully")
            except:
                print("  - Failed to convert to bytes, may not be properly base64-encoded")
                encrypted_bytes = encrypted_password.encode()
        else:
            encrypted_bytes = encrypted_password
            print("  - Password is already stored as bytes")
        
    # Create new encryption key
    print("\nCreating new encryption key...")
    key = Fernet.generate_key()
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)
    print(f"New key created and saved to secret.key")
    
    # Set up Fernet with new key
    fernet = Fernet(key)
    
    # Ask user what to do
    print("\nDo you want to set a new password for all accounts? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        new_password = input("Enter new password for all accounts: ")
        
        # Update passwords
        for account in accounts:
            try:
                # Encrypt new password
                encrypted_password = fernet.encrypt(new_password.encode())
                
                # Update account
                account.password_encrypted = encrypted_password
                print(f"Updated password for {account.username}")
            except Exception as e:
                print(f"Failed to update password for {account.username}: {str(e)}")
        
        # Commit changes
        db.session.commit()
        print("All passwords updated successfully")
    else:
        print("No changes made to passwords")