# create_test_account.py
from app import create_app, db
from app.services.instagram.account import InstagramAccountService
from app.models import InstagramAccount

app = create_app()

with app.app_context():
    # Create account service with fresh encryption
    account_service = InstagramAccountService()
    
    username = input("Enter Instagram username: ")
    password = input("Enter Instagram password: ")
    
    # Delete existing account if it exists
    existing = InstagramAccount.query.filter_by(username=username).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        print(f"Deleted existing account {username}")
    
    # Add account
    result = account_service.add_account(username, password)
    print(f"Account added with result: {result}")
    
    # Activate account
    account_service.update_account_status(username, True)
    print(f"Account {username} activated")
    
    # Test decryption
    account = InstagramAccount.query.filter_by(username=username).first()
    if account:
        try:
            decrypted = account_service.decrypt_password(account.password_encrypted)
            print(f"Password decryption test successful")
            print(f"Decrypted password: '{decrypted[:2]}{'*' * (len(decrypted)-4)}{decrypted[-2:]}'")
        except Exception as e:
            print(f"Decryption test failed: {str(e)}")