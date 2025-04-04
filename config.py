# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # MySQL Database Config
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')
    
    # SQLAlchemy Config using mysql-connector
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://tonirodriguez:Password1234@127.0.0.1:13306/tonirodriguez$socialmediabot'
    SQLALCHEMY_TRACK_MODIFICATIONS = False