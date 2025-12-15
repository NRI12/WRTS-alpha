import os

class ModalConfig:
    """Cấu hình cho Modal deployment"""
    
    # App Configuration
    APP_NAME = os.getenv("MODAL_APP_NAME", "ai-server")
    
    # Python & Base Image
    PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.11")
    
    # System Packages
    SYSTEM_PACKAGES = [
        "ffmpeg",
        "libsm6",
        "libxext6"
    ]
    
    # Python Packages
    PYTHON_PACKAGES = [
        "opencv-python>=4.12.0",
        "ultralytics>=8.0.0",
        "scipy>=1.9.0",
        "fastdtw>=0.3.4",
        "Pillow>=9.0.0",
        "numpy>=2.0.0",
        "gdown>=4.7.0",
        "fastapi>=0.104.0"
    ]
    
    # Model Configuration
    MODELS_DIR = os.getenv("MODELS_DIR", "/root/models")
    WEAPON_MODEL_DIR = os.getenv("WEAPON_MODEL_DIR", "weapon_detection")
    WEAPON_MODEL_FILE = os.getenv("WEAPON_MODEL_FILE", "best.pt")
    
    # Google Drive Model (sensitive - từ .env)
    GOOGLE_DRIVE_FILE_ID = os.getenv("GOOGLE_DRIVE_FILE_ID", "")
    
    # Local Directory Paths
    LOCAL_APP_DIR = os.getenv("LOCAL_APP_DIR", "app")
    REMOTE_APP_PATH = os.getenv("REMOTE_APP_PATH", "/root/app")
    
    # Function Configuration
    HEALTH_CONCURRENT_INPUTS = int(os.getenv("HEALTH_CONCURRENT_INPUTS", "100"))
    HEALTH_TIMEOUT = int(os.getenv("HEALTH_TIMEOUT", "600"))
    HEALTH_CONTAINER_IDLE_TIMEOUT = int(os.getenv("HEALTH_CONTAINER_IDLE_TIMEOUT", "300"))
    
    WEAPON_DETECT_CONCURRENT_INPUTS = int(os.getenv("WEAPON_DETECT_CONCURRENT_INPUTS", "50"))
    WEAPON_DETECT_TIMEOUT = int(os.getenv("WEAPON_DETECT_TIMEOUT", "1200"))
    WEAPON_DETECT_CONTAINER_IDLE_TIMEOUT = int(os.getenv("WEAPON_DETECT_CONTAINER_IDLE_TIMEOUT", "300"))
    
    POSE_CONCURRENT_INPUTS = int(os.getenv("POSE_CONCURRENT_INPUTS", "20"))
    POSE_TIMEOUT = int(os.getenv("POSE_TIMEOUT", "1800"))
    POSE_CONTAINER_IDLE_TIMEOUT = int(os.getenv("POSE_CONTAINER_IDLE_TIMEOUT", "300"))
    
    # Environment Variables for Container
    YOLO_MODELS_DIR = os.getenv("YOLO_MODELS_DIR", "/root/models")

