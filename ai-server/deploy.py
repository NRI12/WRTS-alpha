import os
import modal
from modal import Image, App, web_endpoint, asgi_app
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import shutil

# Load environment variables từ .env file (nếu có python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install it with: pip install python-dotenv")
    print("Continuing without .env file support...")

from config import ModalConfig


def download_model():
    import gdown
    import os
    import sys

    # Đảm bảo /root trong Python path để import config
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")

    from config import ModalConfig

    models_dir = ModalConfig.MODELS_DIR
    weapon_model_dir = ModalConfig.WEAPON_MODEL_DIR
    weapon_model_file = ModalConfig.WEAPON_MODEL_FILE
    file_id = ModalConfig.GOOGLE_DRIVE_FILE_ID

    os.makedirs(f"{models_dir}/{weapon_model_dir}", exist_ok=True)
    model_path = f"{models_dir}/{weapon_model_dir}/{weapon_model_file}"

    if not os.path.exists(model_path):
        if not file_id:
            raise ValueError("GOOGLE_DRIVE_FILE_ID không được để trống trong .env file")
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, model_path, quiet=False)
    return model_path


# Build image với cấu hình từ config
# Đọc tất cả environment variables từ .env và set vào image
env_vars = {
    "YOLO_MODELS_DIR": ModalConfig.YOLO_MODELS_DIR,
    "PYTHONPATH": "/root",
    "MODAL_APP_NAME": ModalConfig.APP_NAME,
    "PYTHON_VERSION": ModalConfig.PYTHON_VERSION,
    "MODELS_DIR": ModalConfig.MODELS_DIR,
    "WEAPON_MODEL_DIR": ModalConfig.WEAPON_MODEL_DIR,
    "WEAPON_MODEL_FILE": ModalConfig.WEAPON_MODEL_FILE,
    "GOOGLE_DRIVE_FILE_ID": ModalConfig.GOOGLE_DRIVE_FILE_ID,
    "LOCAL_APP_DIR": ModalConfig.LOCAL_APP_DIR,
    "REMOTE_APP_PATH": ModalConfig.REMOTE_APP_PATH,
    "HEALTH_CONCURRENT_INPUTS": str(ModalConfig.HEALTH_CONCURRENT_INPUTS),
    "HEALTH_TIMEOUT": str(ModalConfig.HEALTH_TIMEOUT),
    "HEALTH_CONTAINER_IDLE_TIMEOUT": str(ModalConfig.HEALTH_CONTAINER_IDLE_TIMEOUT),
    "WEAPON_DETECT_CONCURRENT_INPUTS": str(ModalConfig.WEAPON_DETECT_CONCURRENT_INPUTS),
    "WEAPON_DETECT_TIMEOUT": str(ModalConfig.WEAPON_DETECT_TIMEOUT),
    "WEAPON_DETECT_CONTAINER_IDLE_TIMEOUT": str(ModalConfig.WEAPON_DETECT_CONTAINER_IDLE_TIMEOUT),
    "POSE_CONCURRENT_INPUTS": str(ModalConfig.POSE_CONCURRENT_INPUTS),
    "POSE_TIMEOUT": str(ModalConfig.POSE_TIMEOUT),
    "POSE_CONTAINER_IDLE_TIMEOUT": str(ModalConfig.POSE_CONTAINER_IDLE_TIMEOUT),
}

image = (
    Image.debian_slim(python_version=ModalConfig.PYTHON_VERSION)
    .apt_install(*ModalConfig.SYSTEM_PACKAGES)
    .pip_install(*ModalConfig.PYTHON_PACKAGES)
    .add_local_file("config.py", remote_path="/root/config.py", copy=True)
    .env(env_vars)
    .run_function(download_model)
    .add_local_dir(ModalConfig.LOCAL_APP_DIR, remote_path=ModalConfig.REMOTE_APP_PATH)
)

app = App(ModalConfig.APP_NAME)

# Tạo FastAPI app
web_app = FastAPI()


# ===== WEAPON DETECTION =====
@web_app.post("/weapon/detect")
async def weapon_detect_endpoint(video: UploadFile = File(...)):
    from app.services.weapon_detection.weapon_detector import WeaponDetector

    temp_dir = tempfile.mkdtemp()
    try:
        video_path = os.path.join(temp_dir, video.filename or "video.mp4")
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)

        result = WeaponDetector.detect_from_video(video_path)
        return result
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ===== EXTRACT TEMPLATE =====
@web_app.post("/pose/extract-template")
async def extract_template_endpoint(video: UploadFile = File(...)):
    from app.services.pose_scoring.pose_scorer import PoseScorer
    import numpy as np
    import base64

    temp_dir = tempfile.mkdtemp()
    try:
        video_path = os.path.join(temp_dir, video.filename or "video.mp4")
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)

        template = PoseScorer.extract_template_from_video(video_path)
        template_bytes = template.tobytes()
        template_b64 = base64.b64encode(template_bytes).decode("utf-8")

        return {
            "template": template_b64,
            "shape": template.shape,
            "dtype": str(template.dtype),
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ===== POSE SCORE =====
@web_app.post("/pose/score")
async def pose_score_endpoint(
    student_video: UploadFile = File(...),
    teacher_template: UploadFile = File(...),
):
    from app.services.pose_scoring.pose_scorer import PoseScorer
    import numpy as np

    temp_dir = tempfile.mkdtemp()
    try:
        # Save student video
        student_path = os.path.join(temp_dir, student_video.filename or "student.mp4")
        with open(student_path, "wb") as f:
            f.write(await student_video.read())

        # Save teacher template
        template_path = os.path.join(
            temp_dir, teacher_template.filename or "template.npy"
        )
        with open(template_path, "wb") as f:
            f.write(await teacher_template.read())

        # Score
        result = PoseScorer.score_video(student_path, template_path)

        # Convert numpy types to Python native types
        def convert_to_native(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            return obj

        result = convert_to_native(result)
        return result

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ===== MOUNT FASTAPI =====
@app.function(
    image=image,
    gpu="T4",
    allow_concurrent_inputs=50,
    timeout=1800,
    container_idle_timeout=300,
)
@asgi_app()
def fastapi_app():
    return web_app


# ===== HEALTH CHECK (giữ nguyên) =====
@app.function(image=image, timeout=60)
@web_endpoint(method="GET", label="health")
def health():
    return {"status": "ok", "service": "ai-server"}
