# fix_account.py
from app import create_app, db
from app.models import InstagramAccount
from cryptography.fernet import Fernet
import os

app = create_app()

with app.app_context():
    # Get the account
    account = InstagramAccount.query.filter_by(username='harmony').first()
    
    if not account:
        print("Account 'harmony' not found")
        exit()
    
    print(f"Found account: {account.username}")
    
    # Generate a fresh key if needed
    if not os.path.exists('secret.key'):
        key = Fernet.generate_key()
        with open('secret.key', 'wb') as key_file:
            key_file.write(key)
        print("Created new encryption key")
    else:
        with open('secret.key', 'rb') as key_file:
            key = key_file.read()
        print("Using existing encryption key")
    
    # Create Fernet instance
    fernet = Fernet(key)
    
    # Set a temporary password
    temp_password = "TemporaryPassword123"
    
    # Encrypt it
    encrypted_password = fernet.encrypt(temp_password.encode())
    
    # Update account
    account.password_encrypted = encrypted_password
    account.is_verified = False
    if hasattr(account, 'verification_status'):
        account.verification_status = 'pending'
    if hasattr(account, 'verification_error'):    
        account.verification_error = None
    db.session.commit()
    
    print(f"Reset password for {account.username} to: {temp_password}")
    print("You should change this password immediately through the web interface.")