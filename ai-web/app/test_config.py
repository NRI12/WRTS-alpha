"""Test configuration for pytest"""
import os
from datetime import timedelta

class TestConfig:
    """Configuration for testing environment"""
    # Database - Use MySQL for production-like testing
    # IMPORTANT: Test on real MySQL to catch ENUM, constraint, and MySQL-specific issues
    # SQLite was only a temporary workaround for concurrent DDL errors
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'mysql+pymysql://root:password@localhost/AI_WRTS_TEST'  # Real MySQL test database
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_reset_on_return': 'commit',
    }
    
    # Testing
    TESTING = True
    
    # Secret Key
    SECRET_KEY = 'test-secret-key-for-testing-only'
    
    # CSRF
    WTF_CSRF_ENABLED = False
    
    # Upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    MAX_VIDEO_SIZE = 500 * 1024 * 1024
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

