#!/usr/bin/env python
"""
Reset Instagram Account Password Script

This script allows you to reset the password for a specific Instagram account
in your database, fixing issues with encrypted passwords.
"""

import argparse
import os
from cryptography.fernet import Fernet

def reset_account_password(username, new_password=None):
    """
    Reset the password for a specified Instagram account
    
    Args:
        username: The Instagram account username
        new_password: Optional new password (will be generated if not provided)
    """
    try:
        # Import app modules
        from app import create_app, db
        from app.models import InstagramAccount
        
        # Create a Flask app context
        app = create_app()
        with app.app_context():
            # Find the account
            account = InstagramAccount.query.filter_by(username=username).first()
            if not account:
                print(f"❌ Error: Account '{username}' not found in database")
                return False
            
            print(f"✅ Found account: {username}")
            
            # Generate a password if not provided
            if not new_password:
                import random
                import string
                new_password = ''.join(random.choices(
                    string.ascii_letters + string.digits + '!@#$%^&*', k=12))
            
            # Initialize Fernet with the existing key
            if not os.path.exists('secret.key'):
                print("❌ Error: secret.key file not found!")
                return False
                
            with open('secret.key', 'rb') as key_file:
                key = key_file.read()
            
            fernet = Fernet(key)
            
            # Encrypt the new password
            encrypted_password = fernet.encrypt(new_password.encode())
            
            # Update the account
            old_encrypted = account.password_encrypted
            account.password_encrypted = encrypted_password
            
            # Save changes
            db.session.commit()
            
            print(f"✅ Password for {username} has been reset")
            print(f"New password: {new_password}")
            print("Please update your records with this new password.")
            
            # Test decryption to confirm it worked
            try:
                decrypted = fernet.decrypt(account.password_encrypted)
                if decrypted.decode() == new_password:
                    print("✅ Decryption test successful - password was saved correctly")
                else:
                    print("❌ Warning: Decryption test returned unexpected result")
            except Exception as e:
                print(f"❌ Warning: Decryption test failed: {str(e)}")
                
            return True
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Reset Instagram Account Password')
    parser.add_argument('username', help='The username of the account to reset')
    parser.add_argument('--password', help='New password (will be generated if not provided)')
    
    args = parser.parse_args()
    
    print(f"=== Reset Password for Instagram Account: {args.username} ===")
    reset_account_password(args.username, args.password)

if __name__ == "__main__":
    main()