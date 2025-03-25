import os
from datetime import timedelta

class Config:
    # MySQL Database configuration
    # Format: mysql+pymysql://username:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/securestore'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = 'EZ5TFPOWO5KHZ2JPJF5JYBSHJ3VG3RUB'  # Change this to a secure secret key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=10)
    
    # 2FA configuration
    TOTP_SECRET_LENGTH = 32 