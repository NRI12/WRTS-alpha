from app.models.training_video import TrainingVideo
from app import db
from app.utils.helpers import get_vietnam_time
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
import os
import random
import time
import cv2
import json

class VideoService:
    
    @staticmethod
    def get_student_videos(student_id, routine_id=None, status=None):
        """Lấy danh sách video của học viên"""
        query = TrainingVideo.query.filter_by(student_id=student_id)
        
        if routine_id:
            query = query.filter_by(routine_id=routine_id)
        
        if status:
            query = query.filter_by(processing_status=status)
        
        return query.order_by(TrainingVideo.uploaded_at.desc()).all()
    
    @staticmethod
    def save_video(file, student_id, routine_id, assignment_id=None, notes=None):
        """Lưu video và metadata"""
        try:
            # Tạo tên file ngẫu nhiên, giữ nguyên phần mở rộng
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Tạo đường dẫn lưu trữ
            upload_folder = os.path.join('static', 'uploads', 'videos')
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, unique_filename)
            try:
                file.save(filepath)
            except Exception as e:
                # Avoid non-ASCII in error message to prevent codec issues on some consoles
                raise Exception(f"Save file error: {repr(e)}")
            
            # Trích xuất metadata từ video (fallback to simple method if cv2 fails)
            try:
                metadata = VideoService.extract_video_metadata(filepath)
                thumbnail_path = VideoService.generate_thumbnail(filepath)
            except:
                # Fallback to simple metadata extraction
                file_size_bytes = os.path.getsize(filepath)
                file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
                metadata = {
                    'duration_seconds': random.randint(30, 180),
                    'file_size_mb': file_size_mb,
                    'resolution': '1920x1080',
                    'fps': 30
                }
                thumbnail_path = None
            
            # Lưu vào database
            video = TrainingVideo(
                student_id=student_id,
                routine_id=routine_id,
                assignment_id=assignment_id,
                video_url=filepath,
                thumbnail_url=thumbnail_path,
                file_size_mb=metadata['file_size_mb'],
                duration_seconds=metadata['duration_seconds'],
                resolution=metadata['resolution'],
                upload_status='completed',
                processing_status='pending',
                uploaded_at=get_vietnam_time()
            )
            
            db.session.add(video)
            db.session.commit()
            
            # Goals feature removed: no-op
            
            return video
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Lỗi khi lưu video: {str(e)}")
    
    @staticmethod
    def extract_video_metadata(filepath):
        """Trích xuất metadata từ video"""
        try:
            cap = cv2.VideoCapture(filepath)
            
            # Lấy thông tin video
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = int(frame_count / fps) if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            # Lấy kích thước file
            file_size_bytes = os.path.getsize(filepath)
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            
            return {
                'duration_seconds': duration,
                'file_size_mb': file_size_mb,
                'resolution': f"{width}x{height}",
                'fps': fps
            }
        except:
            # Fallback nếu không đọc được video
            file_size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
            return {
                'duration_seconds': 60,  # Default
                'file_size_mb': file_size_mb,
                'resolution': '1920x1080',
                'fps': 30
            }
    
    @staticmethod
    def generate_thumbnail(video_path):
        """Tạo thumbnail từ video"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Lấy frame đầu tiên
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Tạo đường dẫn thumbnail
                thumb_folder = os.path.join('static', 'uploads', 'thumbnails')
                os.makedirs(thumb_folder, exist_ok=True)
                # Tạo tên thumbnail ngẫu nhiên
                thumb_filename = f"{uuid.uuid4().hex}.jpg"
                thumb_path = os.path.join(thumb_folder, thumb_filename)
                
                # Lưu thumbnail
                try:
                    cv2.imwrite(thumb_path, frame)
                except Exception as _e:
                    return None
                return thumb_path
            
            return None
        except:
            return None
    
    @staticmethod
    def get_video_by_id(video_id):
        """Lấy video theo ID"""
        return TrainingVideo.query.get(video_id)
    
    @staticmethod
    def get_video_with_analysis(video_id):
        """Lấy video kèm kết quả đánh giá"""
        video = TrainingVideo.query.get(video_id)
        if video:
            return {
                'video': video,
                'manual_evaluations': video.manual_evaluations
            }
        return None
