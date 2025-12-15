import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    _default_db_url = 'mysql+pymysql://root:ryfSkUaebozmfXkiWfkpqARQSESizcED@yamanote.proxy.rlwy.net:32083/railway'
    _mysql_public_url = os.getenv('MYSQL_PUBLIC_URL') or os.getenv('DATABASE_URL') or _default_db_url
    if _mysql_public_url and _mysql_public_url.startswith('mysql://'):
        _mysql_public_url = _mysql_public_url.replace('mysql://', 'mysql+pymysql://', 1)
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or _mysql_public_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
    
    # Upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    MAX_VIDEO_SIZE = 500 * 1024 * 1024
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Railway Storage (S3-compatible)
    RAILWAY_STORAGE_ENDPOINT = os.getenv('RAILWAY_STORAGE_ENDPOINT', 'https://storage.railway.app')
    RAILWAY_STORAGE_ACCESS_KEY = os.getenv('RAILWAY_STORAGE_ACCESS_KEY', 'tid_xxuwPvHGiDiCbzABTY_yhjcMYcaCDDUMbhvJkKQhhpnmbwtGLC')
    RAILWAY_STORAGE_SECRET_KEY = os.getenv('RAILWAY_STORAGE_SECRET_KEY', 'tsec_Q34ue+6+fCGgsiUUtzm6W6slSp6u-sPi7HDtDfCYDJVsBIq5slzxHIzj1QR1dMmzU7i6yb')
    RAILWAY_STORAGE_BUCKET = os.getenv('RAILWAY_STORAGE_BUCKET', 'spacious-tin-gfxskifthjd')
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)