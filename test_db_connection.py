import pymysql
import sys

# List of credential combinations to try
credential_sets = [
    {
        'name': 'Default credentials',
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'tonirodriguez',
        'password': 'Harmo36840568',
        'database': 'tonirodriguez$socialmediabot'
    },
    {
        'name': 'Using database name without username prefix',
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'tonirodriguez',
        'password': 'Harmo36840568',
        'database': 'socialmediabot'
    },
    {
        'name': 'Using database name from comments',
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'g304975_social_user',
        'password': 'Harmo36840568',
        'database': 'g304975_social'
    },
    {
        'name': 'Using commented credentials',
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'g304975_social_user',
        'password': 'Harmo36840568',
        'database': 'tonirodriguez$socialmediabot'
    },
    {
        'name': 'Using socialmediabot alternative',
        'host': '127.0.0.1',
        'port': 13306,
        'user': 'tonirodriguez',
        'password': 'Harmo36840568',
        'database': 'tonirodriguez$socialmediabot'
    }
]

def test_connection(config):
    try:
        print(f"\nTrying: {config['name']}")
        print(f"Host: {config['host']}:{config['port']}")
        print(f"User: {config['user']}")
        print(f"Database: {config['database']}")
        
        # Create connection config without the name field
        conn_config = {k: v for k, v in config.items() if k != 'name'}
        
        # Add charset and cursor class
        conn_config['charset'] = 'utf8mb4'
        conn_config['cursorclass'] = pymysql.cursors.DictCursor
        
        # Attempt connection
        print("Attempting to connect...")
        connection = pymysql.connect(**conn_config)
        
        with connection.cursor() as cursor:
            # Show tables in the database
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print("CONNECTION SUCCESSFUL! Tables in database:")
                for table in tables:
                    # The key name varies based on the MySQL server
                    table_name = list(table.values())[0]
                    print(f"- {table_name}")
            else:
                print("CONNECTION SUCCESSFUL! The database exists but has no tables.")
        
        connection.close()
        print("Connection closed.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("MySQL Credentials Test Script")
    print("=============================")
    
    success = False
    
    for creds in credential_sets:
        if test_connection(creds):
            success = True
            print(f"\n✅ SUCCESS WITH: {creds['name']}")
            print(f"✅ Use these credentials in your application:")
            print(f"✅ Host: {creds['host']}")
            print(f"✅ Port: {creds['port']}")
            print(f"✅ User: {creds['user']}")
            print(f"✅ Database: {creds['database']}")
            print(f"✅ Password: {creds['password']}")
            break
    
    if not success:
        print("\n❌ All credential combinations failed.")
        print("Please verify your PythonAnywhere MySQL credentials:")
        print("1. Log in to PythonAnywhere")
        print("2. Go to the 'Databases' tab")
        print("3. Check your MySQL username and password")
        print("4. Make sure your account supports external MySQL connections")
    
    sys.exit(0 if success else 1)