#!/usr/bin/env python
"""
Quick Account Fix - Resets password for a specific Instagram account

USAGE:
  python quick_account_fix.py

This script will:
1. Find the account "Harmonyimwirigi" in your database
2. Generate a new password and encrypt it with your current key
3. Save the updated password to the database
4. Show you the new password to use
"""

from app import create_app, db
from app.models import InstagramAccount
from cryptography.fernet import Fernet
import os
import random
import string

# Generate a new password
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(random.choice(chars) for _ in range(length))

# Create Flask app context
app = create_app()
with app.app_context():
    try:
        # Find the account
        username = "Harmonyimwirigi"  # Change this if needed
        print(f"Looking for account: {username}")
        
        account = InstagramAccount.query.filter_by(username=username).first()
        if not account:
            print(f"ERROR: Account '{username}' not found in database!")
            exit(1)
        
        print(f"Account found: {username}")
        
        # Generate new password
        new_password = generate_password()
        print(f"Generated new password: {new_password}")
        
        # Get current encryption key
        with open('secret.key', 'rb') as key_file:
            key = key_file.read()
        
        # Create Fernet with current key
        fernet = Fernet(key)
        
        # Encrypt new password
        encrypted_password = fernet.encrypt(new_password.encode())
        print("New password encrypted successfully")
        
        # Save to database
        account.password_encrypted = encrypted_password
        db.session.commit()
        print("Database updated successfully")
        
        # Verify we can decrypt it
        try:
            decrypted = fernet.decrypt(account.password_encrypted)
            if decrypted.decode() == new_password:
                print("Decryption test successful!")
            else:
                print("WARNING: Decryption returned unexpected result!")
        except Exception as e:
            print(f"WARNING: Decryption test failed: {str(e)}")
        
        print("\n========== PASSWORD UPDATED ==========")
        print(f"USERNAME: {username}")
        print(f"NEW PASSWORD: {new_password}")
        print("======================================")
        print("Make sure to save this password somewhere secure!")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        db.session.rollback()