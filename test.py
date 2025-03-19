# test_connection.py
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def test_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', 3306))  # Fixed missing parenthesis here
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"Successfully connected to MySQL Server version {db_info}")
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print(f"Connected to database: {record[0]}")
            return True
            
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        print("\nConnection Details:")
        print(f"Host: {os.getenv('MYSQL_HOST')}")
        print(f"User: {os.getenv('MYSQL_USER')}")
        print(f"Database: {os.getenv('MYSQL_DB')}")
        print(f"Port: {os.getenv('MYSQL_PORT')}")
        return False
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

if __name__ == "__main__":
    test_mysql_connection()