from app.models import db
from app.models.manual_evaluation import ManualEvaluation
from app.models.training_video import TrainingVideo
from app.models.notification import Notification
from app.utils.helpers import get_vietnam_time
from datetime import datetime

class EvaluationService:
    
    @staticmethod
    def get_pending_submissions(instructor_id):
        """Lấy danh sách video chờ chấm điểm"""
        from app.models.assignment import Assignment
        from app.models.class_enrollment import ClassEnrollment
        
        # Lấy tất cả lớp của giảng viên
        from app.models.class_model import Class
        instructor_classes = Class.query.filter_by(
            instructor_id=instructor_id,
            is_active=True
        ).all()
        
        class_ids = [c.class_id for c in instructor_classes]
        
        # Lấy học viên trong các lớp
        enrollments = ClassEnrollment.query.filter(
            ClassEnrollment.class_id.in_(class_ids),
            ClassEnrollment.enrollment_status == 'active'
        ).all()
        
        student_ids = [e.student_id for e in enrollments]
        
        # Lấy video chưa được chấm điểm thủ công
        videos = TrainingVideo.query.filter(
            TrainingVideo.student_id.in_(student_ids),
            TrainingVideo.processing_status == 'completed'
        ).all()
        
        # Filter những video chưa có manual evaluation
        pending = []
        for video in videos:
            if not video.manual_evaluations:
                pending.append(video)
        
        return sorted(pending, key=lambda x: x.uploaded_at, reverse=True)
    
    @staticmethod
    def get_all_submissions(instructor_id):
        """Lấy tất cả video (cả đã chấm và chưa chấm)"""
        from app.models.assignment import Assignment
        from app.models.class_enrollment import ClassEnrollment
        
        # Lấy tất cả lớp của giảng viên
        from app.models.class_model import Class
        instructor_classes = Class.query.filter_by(
            instructor_id=instructor_id,
            is_active=True
        ).all()
        
        class_ids = [c.class_id for c in instructor_classes]
        
        # Lấy học viên trong các lớp
        enrollments = ClassEnrollment.query.filter(
            ClassEnrollment.class_id.in_(class_ids),
            ClassEnrollment.enrollment_status == 'active'
        ).all()
        
        student_ids = [e.student_id for e in enrollments]
        
        # Lấy tất cả video
        videos = TrainingVideo.query.filter(
            TrainingVideo.student_id.in_(student_ids),
            TrainingVideo.processing_status == 'completed'
        ).all()
        
        return sorted(videos, key=lambda x: x.uploaded_at, reverse=True)
    
    @staticmethod
    def create_evaluation(video_id, instructor_id, data):
        """Tạo đánh giá thủ công (chỉ tạo mới, không cho phép trùng)"""
        video = TrainingVideo.query.get(video_id)
        if not video:
            return {'success': False, 'message': 'Không tìm thấy video'}
        
        # Kiểm tra đã có đánh giá chưa
        existing = ManualEvaluation.query.filter_by(
            video_id=video_id,
            instructor_id=instructor_id
        ).first()
        
        if existing:
            return {'success': False, 'message': 'Bạn đã chấm điểm video này rồi'}
        
        evaluation = ManualEvaluation(
            video_id=video_id,
            instructor_id=instructor_id,
            overall_score=data['overall_score'],
            technique_score=data.get('technique_score'),
            posture_score=data.get('posture_score'),
            spirit_score=data.get('spirit_score'),
            comments=data.get('comments'),
            strengths=data.get('strengths'),
            improvements_needed=data.get('improvements_needed'),
            is_passed=data.get('is_passed', False),
            evaluation_method='manual',
            evaluated_at=get_vietnam_time()
        )
        
        db.session.add(evaluation)
        
        # Gửi thông báo cho học viên
        notification = Notification(
            recipient_id=video.student_id,
            sender_id=instructor_id,
            notification_type='evaluation',
            title='Giảng viên đã chấm điểm video của bạn',
            content=f'Video bài "{video.routine.routine_name}" đã được chấm điểm: {data["overall_score"]}/100',
            related_entity_id=video_id,
            related_entity_type='video'
        )
        db.session.add(notification)
        
        db.session.commit()
        return {'success': True, 'evaluation': evaluation}
    
    
    @staticmethod
    def get_evaluation_by_video(video_id):
        """Lấy đánh giá theo video"""
        return ManualEvaluation.query.filter_by(video_id=video_id).all()

    @staticmethod
    def get_evaluation_for_instructor(video_id, instructor_id):
        """Lấy đánh giá của một giảng viên cho video (nếu có)"""
        return ManualEvaluation.query.filter_by(
            video_id=video_id,
            instructor_id=instructor_id
        ).first()

    @staticmethod
    def update_evaluation(evaluation: ManualEvaluation, data: dict):
        """Cập nhật lại đánh giá thủ công hiện có"""
        evaluation.overall_score = data['overall_score']
        evaluation.technique_score = data.get('technique_score')
        evaluation.posture_score = data.get('posture_score')
        evaluation.spirit_score = data.get('spirit_score')
        evaluation.comments = data.get('comments')
        evaluation.strengths = data.get('strengths')
        evaluation.improvements_needed = data.get('improvements_needed')
        evaluation.is_passed = data.get('is_passed', False)
        evaluation.evaluated_at = get_vietnam_time()

        db.session.commit()
        return {'success': True, 'evaluation': evaluation}
