import os
import modal
from modal import Image, App, web_endpoint

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

@app.function(
    image=image, 
    allow_concurrent_inputs=ModalConfig.HEALTH_CONCURRENT_INPUTS, 
    timeout=ModalConfig.HEALTH_TIMEOUT, 
    container_idle_timeout=ModalConfig.HEALTH_CONTAINER_IDLE_TIMEOUT
)
@web_endpoint(method="GET", label="health")
def health():
    return {"status": "ok", "service": ModalConfig.APP_NAME}

@app.function(
    image=image,
    gpu="T4",
    allow_concurrent_inputs=ModalConfig.WEAPON_DETECT_CONCURRENT_INPUTS, 
    timeout=ModalConfig.WEAPON_DETECT_TIMEOUT, 
    container_idle_timeout=ModalConfig.WEAPON_DETECT_CONTAINER_IDLE_TIMEOUT
)
@web_endpoint(method="POST", label="weapon-detect")
async def detect_weapon(request):
    from app.services.weapon_detection.weapon_detector import WeaponDetector
    from fastapi import Request, UploadFile, Form
    import tempfile
    import os
    import shutil
    
    try:
        if isinstance(request, Request):
            content_type = request.headers.get("content-type", "")
            if content_type.startswith("multipart/form-data"):
                form = await request.form()
                if 'video' in form:
                    file = form['video']
                    if isinstance(file, UploadFile):
                        temp_dir = tempfile.mkdtemp()
                        filename = file.filename or "video.mp4"
                        video_path = os.path.join(temp_dir, filename)
                        with open(video_path, 'wb') as f:
                            content = await file.read()
                            f.write(content)
                        try:
                            result = WeaponDetector.detect_from_video(video_path)
                            return result
                        finally:
                            shutil.rmtree(temp_dir, ignore_errors=True)
            else:
                body = await request.json()
                video_path = body.get('video_path')
                if not video_path:
                    return {"error": "video_path is required"}, 400
                if not os.path.exists(video_path):
                    return {"error": f"Video file not found: {video_path}"}, 404
                result = WeaponDetector.detect_from_video(video_path)
                return result
        return {"error": "Invalid request format"}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@app.function(
    image=image, 
    allow_concurrent_inputs=ModalConfig.POSE_CONCURRENT_INPUTS, 
    timeout=ModalConfig.POSE_TIMEOUT, 
    container_idle_timeout=ModalConfig.POSE_CONTAINER_IDLE_TIMEOUT
)
@web_endpoint(method="POST", label="pose-extract-template")
async def extract_template(request):
    from app.services.pose_scoring.pose_scorer import PoseScorer
    from fastapi import Request, UploadFile
    import tempfile
    import os
    import shutil
    import base64
    import numpy as np
    
    try:
        video_path = None
        temp_dir = None
        if isinstance(request, Request):
            content_type = request.headers.get("content-type", "")
            if content_type.startswith("multipart/form-data"):
                form = await request.form()
                if 'video' in form:
                    file = form['video']
                    if isinstance(file, UploadFile):
                        temp_dir = tempfile.mkdtemp()
                        filename = file.filename or "video.mp4"
                        video_path = os.path.join(temp_dir, filename)
                        with open(video_path, 'wb') as f:
                            content = await file.read()
                            f.write(content)
            else:
                body = await request.json()
                video_path = body.get('video_path')
                if not video_path:
                    return {"error": "video_path is required"}, 400
        else:
            return {"error": "Either video file or video_path is required"}, 400
        
        if not video_path or not os.path.exists(video_path):
            return {"error": f"Video file not found: {video_path}"}, 404
        
        template = PoseScorer.extract_template_from_video(video_path)
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        template_path = os.path.join(temp_dir, 'template.npy')
        np.save(template_path, template)
        try:
            with open(template_path, 'rb') as f:
                template_data = f.read()
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            template_base64 = base64.b64encode(template_data).decode('utf-8')
            return {
                'template_base64': template_base64,
                'shape': list(template.shape),
                'dtype': str(template.dtype)
            }
        except Exception as e:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    except Exception as e:
        return {"error": str(e)}, 500

@app.function(
    image=image,
    gpu="T4",
    allow_concurrent_inputs=ModalConfig.POSE_CONCURRENT_INPUTS, 
    timeout=ModalConfig.POSE_TIMEOUT, 
    container_idle_timeout=ModalConfig.POSE_CONTAINER_IDLE_TIMEOUT
)
@web_endpoint(method="POST", label="pose-score")
async def score_pose(request):
    from app.services.pose_scoring.pose_scorer import PoseScorer
    from fastapi import Request, UploadFile
    import tempfile
    import os
    import shutil
    import base64
    
    try:
        student_video_path = None
        teacher_template_path = None
        temp_dir = None
        
        if isinstance(request, Request):
            content_type = request.headers.get("content-type", "")
            if content_type.startswith("multipart/form-data"):
                form = await request.form()
                if 'student_video' in form:
                    file = form['student_video']
                    if isinstance(file, UploadFile):
                        if temp_dir is None:
                            temp_dir = tempfile.mkdtemp()
                        filename = file.filename or "student_video.mp4"
                        student_video_path = os.path.join(temp_dir, filename)
                        with open(student_video_path, 'wb') as f:
                            content = await file.read()
                            f.write(content)
                if 'teacher_template' in form:
                    file = form['teacher_template']
                    if isinstance(file, UploadFile):
                        if temp_dir is None:
                            temp_dir = tempfile.mkdtemp()
                        filename = file.filename or "teacher_template.npy"
                        teacher_template_path = os.path.join(temp_dir, filename)
                        with open(teacher_template_path, 'wb') as f:
                            content = await file.read()
                            f.write(content)
            else:
                body = await request.json()
                if not student_video_path:
                    student_video_path = body.get('student_video_path')
                if not teacher_template_path:
                    teacher_template_path = body.get('teacher_template_path')
                    if not teacher_template_path and 'teacher_template_base64' in body:
                        template_data = base64.b64decode(body['teacher_template_base64'])
                        if temp_dir is None:
                            temp_dir = tempfile.mkdtemp()
                        teacher_template_path = os.path.join(temp_dir, 'teacher_template.npy')
                        with open(teacher_template_path, 'wb') as f:
                            f.write(template_data)
        
        if not student_video_path:
            return {"error": "student_video or student_video_path is required"}, 400
        if not teacher_template_path:
            return {"error": "teacher_template or teacher_template_path is required"}, 400
        if not os.path.exists(student_video_path):
            return {"error": f"Student video not found: {student_video_path}"}, 404
        if not os.path.exists(teacher_template_path):
            return {"error": f"Teacher template not found: {teacher_template_path}"}, 404
        
        result = PoseScorer.score_video(student_video_path, teacher_template_path)
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return result
    except Exception as e:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return {"error": str(e)}, 500
