"""
AI Client Service - Gọi AI server để xử lý AI tasks
Không chứa logic nghiệp vụ, chỉ gọi API và trả về kết quả
"""
import requests
import os
from flask import current_app
import base64


class AIClientService:
    """Client service để gọi AI server API"""
    
    @staticmethod
    def _get_ai_server_url():
        """Lấy URL của AI server từ config hoặc env"""
        return os.getenv('AI_SERVER_URL', 'http://localhost:5001')
    
    @staticmethod
    def detect_weapon(video_path: str) -> dict:
        """
        Gọi AI server để detect weapon từ video
        Args:
            video_path: Đường dẫn đến video file
        Returns:
            dict: Kết quả detection với keys: detected_weapon, confidence, detection_count, total_samples
        """
        ai_server_url = AIClientService._get_ai_server_url()
        endpoint = f"{ai_server_url}/api/v1/weapon/detect"
        
        try:
            # Gửi video_path trong JSON
            response = requests.post(
                endpoint,
                json={'video_path': video_path},
                timeout=300  # 5 minutes timeout cho video processing
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error calling AI server: {e}", flush=True)
            raise Exception(f"Failed to detect weapon: {str(e)}")
    
    @staticmethod
    def extract_template(video_path: str) -> dict:
        """
        Gọi AI server để extract pose template từ video
        Args:
            video_path: Đường dẫn đến video file
        Returns:
            dict: Template data với keys: template_base64, shape, dtype
        """
        ai_server_url = AIClientService._get_ai_server_url()
        endpoint = f"{ai_server_url}/api/v1/pose/extract-template"
        
        try:
            response = requests.post(
                endpoint,
                json={'video_path': video_path},
                timeout=600  # 10 minutes timeout cho template extraction
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error calling AI server: {e}", flush=True)
            raise Exception(f"Failed to extract template: {str(e)}")
    
    @staticmethod
    def score_pose(student_video_path: str, teacher_template_path: str) -> dict:
        """
        Gọi AI server để chấm điểm pose từ video học viên so với template giáo viên
        Args:
            student_video_path: Đường dẫn đến video học viên
            teacher_template_path: Đường dẫn đến template file (.npy) của giáo viên
        Returns:
            dict: Kết quả scoring với keys: total_score, accuracy_score, speed_score, 
                  stability_score, feedback, metrics
        """
        ai_server_url = AIClientService._get_ai_server_url()
        endpoint = f"{ai_server_url}/api/v1/pose/score"
        
        try:
            # Đọc template file và encode base64
            import numpy as np
            template_data = np.load(teacher_template_path)
            
            # Save to bytes
            import io
            template_bytes = io.BytesIO()
            np.save(template_bytes, template_data)
            template_bytes.seek(0)
            template_base64 = base64.b64encode(template_bytes.read()).decode('utf-8')
            
            response = requests.post(
                endpoint,
                json={
                    'student_video_path': student_video_path,
                    'teacher_template_base64': template_base64
                },
                timeout=600  # 10 minutes timeout cho pose scoring
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[AIClientService] Error calling AI server: {e}", flush=True)
            raise Exception(f"Failed to score pose: {str(e)}")
        except Exception as e:
            print(f"[AIClientService] Error preparing template: {e}", flush=True)
            raise Exception(f"Failed to prepare template: {str(e)}")

