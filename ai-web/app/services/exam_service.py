from app.models import db
from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.models.class_enrollment import ClassEnrollment
from app.models.class_model import Class
from app.utils.helpers import get_vietnam_time, get_vietnam_time_naive, vietnam_to_utc
from app.utils.storage_service import StorageService
from datetime import datetime
import uuid
import os
from werkzeug.utils import secure_filename
import cv2
from flask import current_app
from sqlalchemy import or_
from datetime import datetime as dt
import tempfile


class ExamService:
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    MAX_FILE_SIZE = 500 * 1024 * 1024
    
    @staticmethod
    def _validate_video_file(file):
        if not file:
            return False, "Không có file"
        
        filename = secure_filename(file.filename)
        if not ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in ExamService.ALLOWED_EXTENSIONS):
            return False, "Định dạng không hợp lệ (chỉ chấp nhận MP4, AVI, MOV, MKV)"
        
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > ExamService.MAX_FILE_SIZE:
            return False, "File quá lớn (tối đa 500MB)"
        
        return True, filename
    
    @staticmethod
    def _get_video_duration(file_path):
        try:
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = int(frame_count / fps) if fps > 0 else 0
            cap.release()
            return duration
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0
    
    @staticmethod
    def _save_video_file(file, exam_id):
        is_valid, result = ExamService._validate_video_file(file)
        if not is_valid:
            return None, result
        
        filename = result
        temp_filepath = None
        
        try:
            ext = filename.rsplit('.', 1)[1].lower()
            timestamp = int(get_vietnam_time().timestamp())
            new_filename = f"exam_{exam_id}_{timestamp}.{ext}"
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}')
            temp_filepath = temp_file.name
            temp_file.close()

            try:
                file.save(temp_filepath)
            except Exception as e:
                print(f"Error saving file: {repr(e)}")
                return None, "Loi luu file"
            
            duration = ExamService._get_video_duration(temp_filepath)
            
            try:
                file.seek(0)
                video_url = StorageService.upload_file(file, folder='exam_videos', filename=new_filename)
            except Exception as e:
                print(f"Error uploading file to storage: {repr(e)}")
                return None, "Loi upload file"
            
            return video_url, duration
        finally:
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass

    @staticmethod
    def create_exam(data: dict, instructor_id: int, video_file=None):
        if Exam.query.filter_by(exam_code=data['exam_code']).first():
            return {'success': False, 'message': 'Mã bài kiểm tra đã tồn tại'}

        if data['start_time'] < dt.now():
            return {'success': False, 'message': 'Thời gian bắt đầu không được ở quá khứ'}

        exam = Exam(
            exam_code=data['exam_code'],
            exam_name=data['exam_name'],
            description=data.get('description'),
            class_id=data.get('class_id'),
            instructor_id=instructor_id,
            exam_type=data['exam_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_minutes=1,
            pass_score=data.get('pass_score', 70.00),
            max_attempts=1,
            is_published=False,
            video_upload_method=data.get('video_source', 'routine')
        )
        
        if data.get('video_source') == 'routine':
            exam.routine_id = data.get('routine_id')
            if not exam.routine_id:
                return {'success': False, 'message': 'Vui lòng chọn bài võ'}
        
        elif data.get('video_source') == 'upload':
            if not video_file:
                return {'success': False, 'message': 'Vui lòng upload video'}
            
            exam.reference_video_path = 'temp'
        
        else:
            return {'success': False, 'message': 'Phương thức video không hợp lệ'}
        
        try:
            db.session.add(exam)
            db.session.flush()
            
            if data.get('video_source') == 'upload':
                video_url, duration = ExamService._save_video_file(video_file, exam.exam_id)
                if video_url is None:
                    db.session.rollback()
                    return {'success': False, 'message': duration}
                
                exam.reference_video_path = video_url
                exam.video_duration = duration
            
            db.session.commit()
            return {'success': True, 'exam': exam}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Lỗi: {str(e)}'}

    @staticmethod
    def get_exams_by_instructor(instructor_id: int):
        return Exam.query.filter_by(instructor_id=instructor_id).order_by(Exam.created_at.desc()).all()

    @staticmethod
    def get_exam_by_id(exam_id: int):
        return Exam.query.get(exam_id)
    
    @staticmethod
    def verify_exam_access(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra', 'exam': None}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền truy cập bài kiểm tra này', 'exam': None}
        return {'success': True, 'exam': exam}
    
    @staticmethod
    def get_edit_form_data(exam_id: int, instructor_id: int):
        from app.services.routine_service import RoutineService
        from app.services.class_service import ClassService
        
        access_result = ExamService.verify_exam_access(exam_id, instructor_id)
        if not access_result['success']:
            return access_result
        
        exam = access_result['exam']
        
        routines = RoutineService.get_routines_by_instructor(instructor_id, {'is_published': True})
        classes = ClassService.get_classes_by_instructor(instructor_id)
        
        form_data = {
            'exam': exam,
            'routines': routines,
            'classes': classes,
            'video_source': exam.video_upload_method if exam.video_upload_method else 'routine',
            'routine_id': exam.routine_id if exam.video_upload_method == 'routine' else None
        }
        
        return {'success': True, **form_data}

    @staticmethod
    def update_exam(exam_id: int, data: dict, instructor_id: int, video_file=None):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền sửa bài kiểm tra này'}
        
        if data['exam_code'] != exam.exam_code:
            if Exam.query.filter_by(exam_code=data['exam_code']).first():
                return {'success': False, 'message': 'Mã bài kiểm tra đã tồn tại'}
        
        try:
            exam.exam_code = data['exam_code']
            exam.exam_name = data['exam_name']
            exam.description = data.get('description')
            exam.class_id = data.get('class_id')
            exam.exam_type = data['exam_type']
            exam.start_time = data['start_time']
            exam.end_time = data['end_time']
            exam.pass_score = data.get('pass_score', exam.pass_score)
            
            if data['video_source'] == 'routine':
                exam.video_upload_method = 'routine'
                exam.routine_id = data.get('routine_id')
                exam.reference_video_path = None
                exam.video_duration = None
            elif data['video_source'] == 'upload':
                exam.video_upload_method = 'upload'
                exam.routine_id = None
                
                if video_file:
                    video_url, duration = ExamService._save_video_file(video_file, exam.exam_id)
                    if video_url is None:
                        return {'success': False, 'message': duration}
                    exam.reference_video_path = video_url
                    exam.video_duration = duration
            
            db.session.commit()
            return {'success': True, 'exam': exam}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Lỗi khi cập nhật: {str(e)}'}

    @staticmethod
    def publish_exam(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}
        exam.is_published = True
        db.session.commit()
        return {'success': True, 'exam': exam}

    @staticmethod
    def delete_exam(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa'}
        
        result_count = ExamResult.query.filter_by(exam_id=exam_id).count()
        if result_count > 0:
            return {'success': False, 'message': f'Không thể xóa - đã có {result_count} kết quả thi'}
        
        if exam.video_upload_method == 'upload' and exam.reference_video_path:
            try:
                StorageService.delete_file(exam.reference_video_path)
            except Exception as e:
                print(f"Error deleting video file from storage: {e}")
        
        db.session.delete(exam)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_exam_results(exam_id: int):
        return ExamResult.query.filter_by(exam_id=exam_id).order_by(ExamResult.submitted_at.desc()).all()
    
    @staticmethod
    def get_exam_result_by_id(result_id: int):
        return ExamResult.query.get(result_id)
    
    @staticmethod
    def verify_exam_result_access(result_id: int, instructor_id: int):
        result = ExamResult.query.get(result_id)
        if not result:
            return {'success': False, 'message': 'Không tìm thấy kết quả', 'result': None}
        
        exam = Exam.query.get(result.exam_id)
        if not exam or exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền truy cập kết quả này', 'result': None}
        
        return {'success': True, 'result': result, 'exam': exam}
    
    @staticmethod
    def grade_exam_result(result_id: int, score: float, instructor_id: int):
        access_result = ExamService.verify_exam_result_access(result_id, instructor_id)
        if not access_result['success']:
            return access_result
        
        result = access_result['result']
        exam = access_result['exam']
        
        try:
            result.score = score
            result.graded_at = get_vietnam_time()
            if score >= exam.pass_score:
                result.result_status = 'passed'
            else:
                result.result_status = 'failed'
            
            db.session.commit()
            return {'success': True, 'result': result}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Lỗi khi chấm điểm: {str(e)}'}
    
    @staticmethod
    def grade_exam_result_from_evaluation(result_id: int, overall_score: float, instructor_id: int):
        access_result = ExamService.verify_exam_result_access(result_id, instructor_id)
        if not access_result['success']:
            return access_result
        
        result = access_result['result']
        exam = access_result['exam']
        
        try:
            result.score = overall_score
            result.graded_at = get_vietnam_time()
            if overall_score >= exam.pass_score:
                result.result_status = 'passed'
            else:
                result.result_status = 'failed'
            
            db.session.commit()
            return {'success': True, 'result': result}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Lỗi khi cập nhật điểm: {str(e)}'}

    @staticmethod
    def get_exams_for_student(student_id: int):
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        
        query = Exam.query.filter(Exam.is_published == True)
        if class_ids:
            query = query.filter(or_(Exam.class_id.in_(class_ids), Exam.class_id.is_(None)))
        else:
            query = query.filter(Exam.class_id.is_(None))
        
        return query.order_by(Exam.start_time.asc()).all()

    @staticmethod
    def get_class_exams_for_student(student_id: int):
        enrollments = ClassEnrollment.query.filter_by(student_id=student_id).all()
        class_ids = [e.class_id for e in enrollments]
        if not class_ids:
            return []
        return Exam.query.filter(
            Exam.is_published == True,
            Exam.class_id.in_(class_ids)
        ).order_by(Exam.start_time.asc()).all()

    @staticmethod
    def get_student_exam_result(exam_id: int, student_id: int):
        return ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).order_by(ExamResult.attempt_number.desc()).all()

    @staticmethod
    def can_take_exam(exam_id: int, student_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return False, "Không tìm thấy bài kiểm tra"
        
        if not exam.is_published:
            return False, "Bài kiểm tra chưa được xuất bản"
        
        now = get_vietnam_time_naive()
        
        if now < exam.start_time:
            return False, f"Chưa đến giờ thi. Bắt đầu lúc {exam.start_time.strftime('%d/%m/%Y %H:%M')}"
        
        if now > exam.end_time:
            return False, "Đã hết hạn nộp bài"
        
        if exam.class_id:
            enrollment = ClassEnrollment.query.filter_by(
                student_id=student_id,
                class_id=exam.class_id,
                enrollment_status='active'
            ).first()
            
            if not enrollment:
                return False, "Bạn không thuộc lớp học này"
        
        results = ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).all()
        
        if len(results) >= 1:
            return False, "Bạn đã thi bài này rồi"
        
        return True, "OK"
    
    @staticmethod
    def submit_exam_result(exam_id: int, student_id: int, video_file, notes: str = ''):
        from app.services.video_service import VideoService
        
        can_take, message = ExamService.can_take_exam(exam_id, student_id)
        if not can_take:
            return {'success': False, 'message': message}
        
        exam = Exam.query.get(exam_id)
        
        existing_results = ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).all()
        attempt_number = len(existing_results) + 1
        
        try:
            routine_id = exam.routine_id if exam.video_upload_method == 'routine' else None
            
            video = VideoService.save_video(
                file=video_file,
                student_id=student_id,
                routine_id=routine_id,
                assignment_id=None,
                notes=f"Exam: {exam.exam_name} - Lần {attempt_number}"
            )
            
            exam_result = ExamResult(
                exam_id=exam_id,
                student_id=student_id,
                video_id=video.video_id,
                attempt_number=attempt_number,
                submitted_at=get_vietnam_time(),
                score=None,
                instructor_comments=notes,
                graded_at=None
            )
            
            db.session.add(exam_result)
            db.session.commit()
            
            from app.services.weapon_detection_service import WeaponDetectionService
            WeaponDetectionService.detect_async(video.video_id)
            
            return {
                'success': True,
                'message': 'Nộp bài thành công',
                'result': exam_result
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Lỗi khi nộp bài: {str(e)}'
            }

    @staticmethod
    def get_form_prefill_data_for_class(class_id: int, instructor_id: int):
        """Get pre-fill data for exam form when creating from class context"""
        if not class_id:
            return None
        
        class_obj = Class.query.get(class_id)
        if not class_obj or class_obj.instructor_id != instructor_id:
            return None
        
        return {
            'class_id': class_id
        }

    @staticmethod
    def get_upcoming_class_exams(class_id: int, limit: int = 3):
        """Get upcoming exams for a class"""
        from app.utils.helpers import get_vietnam_time_naive
        now = get_vietnam_time_naive()
        return Exam.query.filter_by(
            class_id=class_id
        ).filter(Exam.start_time > now).order_by(Exam.start_time.asc()).limit(limit).all()

    @staticmethod
    def get_recent_class_exams(class_id: int, limit: int = 3):
        """Get recent exams for a class"""
        return Exam.query.filter_by(
            class_id=class_id
        ).order_by(Exam.created_at.desc()).limit(limit).all()

