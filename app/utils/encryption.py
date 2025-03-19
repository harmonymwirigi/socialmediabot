# app/utils/encryption.py
from cryptography.fernet import Fernet
import os
import base64

def get_encryption_key():
    """Get the current encryption key, create if it doesn't exist"""
    key_path = 'secret.key'
    
    if not os.path.exists(key_path):
        # Create a new key
        key = Fernet.generate_key()
        with open(key_path, 'wb') as key_file:
            key_file.write(key)
        print(f"New encryption key created at {key_path}")
    else:
        # Read existing key
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
    
    return key

def reset_password(account):
    """Reset an account's password encryption with the current key"""
    from app import db
    
    # This is a placeholder - in a real app, you'd have a secure way
    # to recover or reset passwords. For now, we'll use a default.
    default_password = "DefaultPassword123"
    
    # Get the current key and create Fernet instance
    key = get_encryption_key()
    fernet = Fernet(key)
    
    # Encrypt with current key
    encrypted_password = fernet.encrypt(default_password.encode())
    
    # Update account
    account.password_encrypted = encrypted_password
    account.is_verified = False
    account.verification_status = 'pending'
    account.verification_error = None
    db.session.commit()
    
    return default_password