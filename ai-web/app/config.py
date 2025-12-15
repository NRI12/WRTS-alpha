import os
from datetime import timedelta

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:password@localhost/AI_WRTS'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    
    # Upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)