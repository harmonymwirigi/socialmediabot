# account_test.py
from app import create_app, db
from app.services.instagram.account import InstagramAccountService
from app.models import InstagramAccount

app = create_app()

with app.app_context():
    # Get the account
    account = InstagramAccount.query.filter_by(username='harmony').first()
    
    if account:
        print(f"Found account: {account.username}")
        
        # Try to decrypt password
        account_service = InstagramAccountService()
        
        try:
            password = account_service.decrypt_password(account.password_encrypted)
            print(f"Password decryption successful: '{password[:2]}{'*' * (len(password)-4)}{password[-2:]}'")
            
            # Create a simple browser test (without full interaction)
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless')  # Run in background
            
            print("Creating simple browser instance...")
            driver = webdriver.Chrome(options=options)
            print("Browser created successfully")
            
            driver.quit()
            print("Browser closed successfully")
            
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("Account 'harmony' not found")