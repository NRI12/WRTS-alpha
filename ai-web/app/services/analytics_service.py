from app.models import db
from app.models.training_history import TrainingHistory
from app.models.training_video import TrainingVideo
from app.models.manual_evaluation import ManualEvaluation
from app.models.class_enrollment import ClassEnrollment
from app.models.class_model import Class
from app.models.user import User
from app.models.assignment import Assignment
from app.utils.helpers import get_vietnam_time, get_vietnam_time_naive
from datetime import datetime, timedelta
from sqlalchemy import func, and_

class AnalyticsService:
    
    # ============ STUDENT ANALYTICS ============
    
    @staticmethod
    def get_student_overview(student_id):
        """Tổng quan học viên"""
        total_videos = TrainingVideo.query.filter_by(student_id=student_id).count()
        
        # Điểm trung bình từ giảng viên
        avg_manual_score = db.session.query(func.avg(ManualEvaluation.overall_score)).join(
            TrainingVideo
        ).filter(TrainingVideo.student_id == student_id).scalar() or 0
        
        # Số lần đạt
        passed_count = ManualEvaluation.query.join(TrainingVideo).filter(
            TrainingVideo.student_id == student_id,
            ManualEvaluation.is_passed == True
        ).count()
        
        return {
            'total_videos': total_videos,
            'avg_manual_score': round(float(avg_manual_score), 2),
            'passed_count': passed_count,
            'pass_rate': round((passed_count / total_videos * 100) if total_videos > 0 else 0, 2)
        }
    
    @staticmethod
    def get_score_progression(student_id, days=30):
        """Biểu đồ điểm số theo thời gian"""
        cutoff_date = get_vietnam_time_naive() - timedelta(days=days)
        
        videos = TrainingVideo.query.filter(
            TrainingVideo.student_id == student_id,
            TrainingVideo.uploaded_at >= cutoff_date
        ).order_by(TrainingVideo.uploaded_at).all()
        
        data = []
        for video in videos:
            manual_score = video.manual_evaluations[0].overall_score if video.manual_evaluations else None
            
            # Safely resolve routine name if available
            routine_name = None
            try:
                if getattr(video, 'routine', None) and getattr(video.routine, 'routine_name', None):
                    routine_name = video.routine.routine_name
                elif getattr(video, 'assignment', None) and getattr(video.assignment, 'routine', None) and getattr(video.assignment.routine, 'routine_name', None):
                    routine_name = video.assignment.routine.routine_name
            except Exception:
                routine_name = None

            data.append({
                'date': video.uploaded_at.strftime('%Y-%m-%d'),
                'routine': routine_name,
                'manual_score': float(manual_score) if manual_score else None
            })
        
        return data
    
    @staticmethod
    def get_routine_completion(student_id):
        """Tỷ lệ hoàn thành bài võ"""
        from app.models.martial_routine import MartialRoutine
        
        all_routines = MartialRoutine.query.filter_by(is_published=True).count()
        
        completed_routines = db.session.query(
            func.count(func.distinct(TrainingVideo.routine_id))
        ).filter(TrainingVideo.student_id == student_id).scalar() or 0
        
        return {
            'total_routines': all_routines,
            'completed': completed_routines,
            'completion_rate': round((completed_routines / all_routines * 100) if all_routines > 0 else 0, 2)
        }
    
    @staticmethod
    def get_strengths_weaknesses(student_id):
        """Phân tích điểm mạnh/yếu (radar chart data)"""
        # Lấy điểm trung bình các tiêu chí từ chấm thủ công
        avg_scores = db.session.query(
            func.avg(ManualEvaluation.technique_score).label('technique'),
            func.avg(ManualEvaluation.posture_score).label('posture'),
            func.avg(ManualEvaluation.spirit_score).label('spirit')
        ).join(TrainingVideo).filter(
            TrainingVideo.student_id == student_id
        ).first()
        
        return {
            'technique': round(float(avg_scores.technique or 0), 2),
            'posture': round(float(avg_scores.posture or 0), 2),
            'spirit': round(float(avg_scores.spirit or 0), 2)
        }
    
    # ============ INSTRUCTOR ANALYTICS ============
    
    @staticmethod
    def get_class_overview(class_id):
        """Tổng quan lớp học"""
        enrollments = ClassEnrollment.query.filter_by(
            class_id=class_id,
            enrollment_status='active'
        ).all()
        
        student_ids = [e.student_id for e in enrollments]
        
        if not student_ids:
            return {
                'total_students': 0,
                'avg_score': 0,
                'completion_rate': 0,
                'pass_rate': 0
            }
        
        # Điểm trung bình lớp: chỉ tính các video thuộc bài tập của lớp này
        class_videos = (
            TrainingVideo.query
            .join(Assignment, TrainingVideo.assignment_id == Assignment.assignment_id)
            .filter(
                TrainingVideo.student_id.in_(student_ids),
                Assignment.assigned_to_class == class_id
            ).all()
        )

        scores = []
        for v in class_videos:
            manual_score = v.manual_evaluations[0].overall_score if v.manual_evaluations else None
            if manual_score is not None:
                scores.append(float(manual_score))

        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        
        # Tỷ lệ hoàn thành (đã nộp video)
        total_assignments = db.session.query(func.count()).select_from(
            db.session.query(TrainingVideo.student_id).filter(
                TrainingVideo.student_id.in_(student_ids)
            ).distinct().subquery()
        ).scalar() or 0
        
        # Tỷ lệ đạt
        passed = ManualEvaluation.query.join(TrainingVideo).filter(
            TrainingVideo.student_id.in_(student_ids),
            ManualEvaluation.is_passed == True
        ).count()
        
        total_evaluated = ManualEvaluation.query.join(TrainingVideo).filter(
            TrainingVideo.student_id.in_(student_ids)
        ).count()
        
        return {
            'total_students': len(student_ids),
            'avg_score': float(avg_score),
            'total_submissions': TrainingVideo.query.filter(
                TrainingVideo.student_id.in_(student_ids)
            ).count(),
            'pass_rate': round((passed / total_evaluated * 100) if total_evaluated > 0 else 0, 2)
        }

    @staticmethod
    def get_student_avg_for_class(student_id: int, class_id: int) -> float:
        """Điểm trung bình của một học viên trong phạm vi các assignment của lớp chỉ định.
        Ưu tiên điểm chấm tay; nếu không có thì dùng điểm AI.
        """
        videos = (
            TrainingVideo.query
            .join(Assignment, TrainingVideo.assignment_id == Assignment.assignment_id)
            .filter(
                TrainingVideo.student_id == student_id,
                Assignment.assigned_to_class == class_id
            ).all()
        )

        scores: list[float] = []
        for v in videos:
            manual_score = v.manual_evaluations[0].overall_score if v.manual_evaluations else None
            if manual_score is not None:
                scores.append(float(manual_score))

        return round(sum(scores) / len(scores), 2) if scores else 0.0
    
    @staticmethod
    def get_student_ranking(class_id):
        """Xếp hạng học viên trong lớp"""
        enrollments = ClassEnrollment.query.filter_by(
            class_id=class_id,
            enrollment_status='active'
        ).all()
        
        student_ids = [e.student_id for e in enrollments]
        
        rankings = []
        for student_id in student_ids:
            student = User.query.get(student_id)
            
            avg_score = db.session.query(func.avg(ManualEvaluation.overall_score)).join(
                TrainingVideo
            ).filter(TrainingVideo.student_id == student_id).scalar() or 0
            
            video_count = TrainingVideo.query.filter_by(student_id=student_id).count()
            
            rankings.append({
                'student': student,
                'avg_score': round(float(avg_score), 2),
                'video_count': video_count
            })
        
        # Sort by avg_score descending
        rankings.sort(key=lambda x: x['avg_score'], reverse=True)
        
        return rankings
    
    @staticmethod
    def get_routine_usage_stats(instructor_id):
        """Thống kê sử dụng bài võ"""
        from app.models.martial_routine import MartialRoutine
        
        routines = MartialRoutine.query.filter_by(instructor_id=instructor_id).all()
        
        stats = []
        for routine in routines:
            video_count = TrainingVideo.query.filter_by(routine_id=routine.routine_id).count()
            
            avg_score = db.session.query(func.avg(ManualEvaluation.overall_score)).join(
                TrainingVideo
            ).filter(TrainingVideo.routine_id == routine.routine_id).scalar() or 0
            
            stats.append({
                'routine': routine,
                'usage_count': video_count,
                'avg_score': round(float(avg_score), 2)
            })
        
        return sorted(stats, key=lambda x: x['usage_count'], reverse=True)
    
    # ============ MANAGER ANALYTICS ============
    
    @staticmethod
    def get_system_overview():
        """Tổng quan toàn hệ thống"""
        total_students = User.query.join(User.role).filter(
            User.role.has(role_code='STUDENT'),
            User.is_active == True
        ).count()
        
        total_instructors = User.query.join(User.role).filter(
            User.role.has(role_code='INSTRUCTOR'),
            User.is_active == True
        ).count()
        
        total_classes = Class.query.filter_by(is_active=True).count()
        total_videos = TrainingVideo.query.count()
        
        # Tỷ lệ đạt toàn hệ thống
        total_evaluated = ManualEvaluation.query.count()
        total_passed = ManualEvaluation.query.filter_by(is_passed=True).count()
        
        return {
            'total_students': total_students,
            'total_instructors': total_instructors,
            'total_classes': total_classes,
            'total_videos': total_videos,
            'total_evaluated': total_evaluated,
            'system_pass_rate': round((total_passed / total_evaluated * 100) if total_evaluated > 0 else 0, 2)
        }
    
    @staticmethod
    def get_instructor_performance():
        """Hiệu suất giảng viên"""
        instructors = User.query.join(User.role).filter(
            User.role.has(role_code='INSTRUCTOR'),
            User.is_active == True
        ).all()
        
        performance = []
        for instructor in instructors:
            classes = Class.query.filter_by(
                instructor_id=instructor.user_id,
                is_active=True
            ).count()
            
            # Lấy tất cả học viên của giảng viên
            enrollments = db.session.query(ClassEnrollment.student_id).join(Class).filter(
                Class.instructor_id == instructor.user_id,
                ClassEnrollment.enrollment_status == 'active'
            ).distinct().all()
            
            student_count = len(enrollments)
            
            # Điểm trung bình của học viên
            student_ids = [e[0] for e in enrollments]
            avg_score = 0
            if student_ids:
                avg_score = db.session.query(func.avg(ManualEvaluation.overall_score)).join(
                    TrainingVideo
                ).filter(TrainingVideo.student_id.in_(student_ids)).scalar() or 0
            
            performance.append({
                'instructor': instructor,
                'total_classes': classes,
                'total_students': student_count,
                'avg_student_score': round(float(avg_score), 2)
            })
        
        return sorted(performance, key=lambda x: x['avg_student_score'], reverse=True)
    
    @staticmethod
    def get_trends_data(days=30):
        """Xu hướng theo thời gian"""
        cutoff_date = get_vietnam_time_naive() - timedelta(days=days)
        
        # Video uploads per day
        videos_by_day = db.session.query(
            func.date(TrainingVideo.uploaded_at).label('date'),
            func.count(TrainingVideo.video_id).label('count')
        ).filter(
            TrainingVideo.uploaded_at >= cutoff_date
        ).group_by(func.date(TrainingVideo.uploaded_at)).all()
        
        # Evaluations per day
        evals_by_day = db.session.query(
            func.date(ManualEvaluation.evaluated_at).label('date'),
            func.count(ManualEvaluation.evaluation_id).label('count')
        ).filter(
            ManualEvaluation.evaluated_at >= cutoff_date
        ).group_by(func.date(ManualEvaluation.evaluated_at)).all()
        
        return {
            'videos': [{'date': str(v.date), 'count': v.count} for v in videos_by_day],
            'evaluations': [{'date': str(e.date), 'count': e.count} for e in evals_by_day]
        }
