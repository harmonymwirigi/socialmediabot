# test_account_service.py
from app import create_app
from app.models import InstagramAccount
from app.services.instagram.account import InstagramAccountService

app = create_app()

with app.app_context():
    # Check accounts in database
    accounts = InstagramAccount.query.all()
    print(f"Found {len(accounts)} accounts in the database")
    
    for account in accounts:
        print(f"- {account.username} (active: {account.is_active})")
    
    # Test account service
    service = InstagramAccountService()
    
    # Check active accounts
    active_accounts = service.get_active_accounts()
    print(f"\nFound {len(active_accounts)} active accounts through service")
    
    for username, _ in active_accounts:
        print(f"- {username}")
    
    # Attempt password decryption for testing
    if active_accounts:
        username, encrypted_password = active_accounts[0]
        try:
            password = service.decrypt_password(encrypted_password)
            masked = password[:2] + '*' * (len(password)-4) + password[-2:]
            print(f"\nSuccessfully decrypted password for {username}: {masked}")
        except Exception as e:
            print(f"\nFailed to decrypt password: {str(e)}")