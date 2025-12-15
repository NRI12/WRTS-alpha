Sự khác biệt Storage URL vs Local Path:
Storage URLLocal PathVí dụhttps://storage.railway.app/bucket/videos/abc.mp4/home/user/uploads/abc.mp4Vị tríFile trên cloud (Railway Storage)File trên máy chủ cụ thểTruy cậpAi cũng download được qua HTTPChỉ server đó truy cập file systemHiện tạiai-web lưu video ở đây ✅Modal tìm file ở đây ❌
Vấn đề:

ai-web upload video → Railway Storage → nhận URL
ai-web gọi Modal với video_path = URL
Modal tìm file tại path đó trong container của Modal → không có → lỗi

Fix cần làm:
File cần sửa: ai-web/app/services/ai_client_service.py
pythonimport requests
import os
from flask import current_app
import base64
from app.utils.storage_service import StorageService

class AIClientService:
    
    @staticmethod
    def detect_weapon(video_url: str) -> dict:
        """
        video_url: URL từ Storage hoặc local path
        """
        ai_server_url = AIClientService._get_ai_server_url()
        endpoint = f"{ai_server_url}/api/v1/weapon/detect"
        
        temp_path = None
        try:
            # Download từ Storage về temp
            if video_url.startswith('https://storage.railway.app'):
                temp_path = StorageService.download_file_to_temp(video_url)
                video_file_path = temp_path
            else:
                video_file_path = video_url
            
            # Upload lên Modal qua multipart
            with open(video_file_path, 'rb') as f:
                files = {'video': ('video.mp4', f, 'video/mp4')}
                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=1200  # 20 phút
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error: {e}", flush=True)
            raise Exception(f"Failed to detect weapon: {str(e)}")
        finally:
            # Xóa temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def extract_template(video_url: str) -> dict:
        ai_server_url = AIClientService._get_ai_server_url()
        endpoint = f"{ai_server_url}/api/v1/pose/extract-template"
        
        temp_path = None
        try:
            if video_url.startswith('https://storage.railway.app'):
                temp_path = StorageService.download_file_to_temp(video_url)
                video_file_path = temp_path
            else:
                video_file_path = video_url
            
            with open(video_file_path, 'rb') as f:
                files = {'video': ('video.mp4', f, 'video/mp4')}
                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=1800  # 30 phút
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error: {e}", flush=True)
            raise Exception(f"Failed to extract template: {str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def score_pose(student_video_url: str, teacher_template_path: str) -> dict:
        ai_server_url = AIClientService._get_ai_server_url()
        endpoint = f"{ai_server_url}/api/v1/pose/score"
        
        temp_video_path = None
        try:
            # Download student video
            if student_video_url.startswith('https://storage.railway.app'):
                temp_video_path = StorageService.download_file_to_temp(student_video_url)
                student_file_path = temp_video_path
            else:
                student_file_path = student_video_url
            
            # Upload cả video và template
            with open(student_file_path, 'rb') as sv, \
                 open(teacher_template_path, 'rb') as tt:
                files = {
                    'student_video': ('student.mp4', sv, 'video/mp4'),
                    'teacher_template': ('template.npy', tt, 'application/octet-stream')
                }
                response = requests.post(
                    endpoint,
                    files=files,
                    timeout=1800
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error: {e}", flush=True)
            raise Exception(f"Failed to score pose: {str(e)}")
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
File cần sửa: ai-server/.env
bashWEAPON_DETECT_TIMEOUT=1200  # 20 phút
POSE_TIMEOUT=1800           # 30 phút
Sau khi fix:

ai-web download video từ Storage → temp file local
Upload temp file → Modal qua multipart/form-data
Modal nhận file và xử lý
ai-web xóa temp file