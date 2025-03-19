# Create this file: app/debug.py
from app import create_app, db
from app.models import InstagramAccount
from app.services.instagram.account import InstagramAccountService

def debug_accounts():
    """Debug account retrieval"""
    app = create_app()
    
    with app.app_context():
        # Check all accounts in the database
        all_accounts = InstagramAccount.query.all()
        print(f"Total accounts in database: {len(all_accounts)}")
        
        for account in all_accounts:
            print(f"  - {account.username}: is_active={account.is_active}, verified={account.verified if hasattr(account, 'verified') else 'N/A'}")
        
        # Try to get active accounts through the service
        account_service = InstagramAccountService()
        active_accounts = account_service.get_active_accounts()
        
        print(f"\nActive accounts from service: {len(active_accounts)}")
        for account in active_accounts:
            print(f"  - {account[0]}")  # account[0] should be username

if __name__ == "__main__":
    debug_accounts()