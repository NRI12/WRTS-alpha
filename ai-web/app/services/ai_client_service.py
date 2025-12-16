import requests
import os
from flask import current_app
from app.utils.storage_service import StorageService


class AIClientService:
    
    @staticmethod
    def _get_ai_server_url():
        url = os.getenv('AI_SERVER_URL', 'http://localhost:5001')
        return url.rstrip('/')
    
    @staticmethod
    def _get_endpoint_url(path: str) -> str:
        ai_server_url = AIClientService._get_ai_server_url()
        return f"{ai_server_url}/{path.lstrip('/')}"
    
    @staticmethod
    def detect_weapon(video_url: str) -> dict:
        endpoint = AIClientService._get_endpoint_url("weapon/detect")
        
        temp_path = None
        try:
            if video_url.startswith('https://storage.railway.app'):
                temp_path = StorageService.download_file_to_temp(video_url)
                video_file_path = temp_path
            else:
                video_file_path = video_url
            
            video_filename = os.path.basename(video_file_path)
            if not video_filename or not video_filename.endswith(('.mp4', '.avi', '.mov')):
                video_filename = 'video.mp4'
            
            print(f"[AIClientService] Calling endpoint: {endpoint}", flush=True)
            print(f"[AIClientService] Video file: {video_filename}", flush=True)
            
            with open(video_file_path, 'rb') as f:
                files = {'video': (video_filename, f, 'video/mp4')}
                data = {}
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=1200
                )
            
            print(f"[AIClientService] Response status: {response.status_code}", flush=True)
            if response.status_code != 200:
                print(f"[AIClientService] Response text: {response.text[:500]}", flush=True)
            
            response.raise_for_status()
            result = response.json()
            print(f"[AIClientService] Response JSON: {result}", flush=True)
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error: {e}", flush=True)
            if hasattr(e, 'response') and e.response is not None:
                print(f"[AIClientService] Response: {e.response.text[:500]}", flush=True)
            raise Exception(f"Failed to detect weapon: {str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    @staticmethod
    def extract_template(video_url: str) -> dict:
        endpoint = AIClientService._get_endpoint_url("pose/extract-template")
        
        temp_path = None
        try:
            if video_url.startswith('https://storage.railway.app'):
                temp_path = StorageService.download_file_to_temp(video_url)
                video_file_path = temp_path
            else:
                video_file_path = video_url
            
            video_filename = os.path.basename(video_file_path)
            if not video_filename or not video_filename.endswith(('.mp4', '.avi', '.mov')):
                video_filename = 'video.mp4'
            
            with open(video_file_path, 'rb') as f:
                files = {'video': (video_filename, f, 'video/mp4')}
                data = {}
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
                    timeout=1800
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
        endpoint = AIClientService._get_endpoint_url("pose/score")
        
        temp_video_path = None
        try:
            if student_video_url.startswith('https://storage.railway.app'):
                temp_video_path = StorageService.download_file_to_temp(student_video_url)
                student_file_path = temp_video_path
            else:
                student_file_path = student_video_url
            
            with open(student_file_path, 'rb') as sv, open(teacher_template_path, 'rb') as tt:
                files = {
                    'student_video': ('student.mp4', sv, 'video/mp4'),
                    'teacher_template': ('template.npy', tt, 'application/octet-stream')
                }
                data = {}
                response = requests.post(
                    endpoint,
                    files=files,
                    data=data,
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

