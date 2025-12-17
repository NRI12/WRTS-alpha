from app.models import db
from app.models.assignment import Assignment
from app.models.martial_routine import MartialRoutine
from app.models.user import User
from app.models.class_enrollment import ClassEnrollment
from app.models.training_video import TrainingVideo
from app.models.class_model import Class


class AssignmentService:
    @staticmethod
    def create_assignment(data: dict, assigned_by: int):
        """Tạo assignment mới - BẮT BUỘC có video"""
        try:
            # VALIDATE: Bắt buộc phải có video
            if not data.get('instructor_video_url'):
                return {'success': False, 'message': 'Vui lòng upload video demo cho bài tập này'}
            
            # Validate that the class is approved if assignment is for a class
            if data.get('assigned_to_class'):
                class_obj = Class.query.get(data['assigned_to_class'])
                if not class_obj:
                    return {'success': False, 'message': 'Không tìm thấy lớp học'}
                if class_obj.approval_status != 'approved':
                    return {'success': False, 'message': 'Chỉ có thể tạo bài tập cho lớp đã được duyệt'}
                if class_obj.instructor_id != assigned_by:
                    return {'success': False, 'message': 'Bạn không có quyền tạo bài tập cho lớp này'}

            assignment = Assignment(
                routine_id=data['routine_id'],
                assigned_by=assigned_by,
                assignment_type=data['assignment_type'],
                assigned_to_student=data.get('assigned_to_student'),
                assigned_to_class=data.get('assigned_to_class'),
                deadline=data.get('deadline'),
                instructions=data.get('instructions'),
                priority=data.get('priority', 'normal'),
                is_mandatory=data.get('is_mandatory', True),
                instructor_video_url=data['instructor_video_url'],  # BẮT BUỘC
                grading_method=data.get('grading_method', 'manual')
            )

            db.session.add(assignment)
            db.session.flush()
            
            # Gửi thông báo
            from app.models.notification import Notification
            if data['assignment_type'] == 'individual':
                notification = Notification(
                    recipient_id=data['assigned_to_student'],
                    sender_id=assigned_by,
                    notification_type='assignment',
                    title='Bài tập mới',
                    content=f'Bạn có bài tập mới với video hướng dẫn',
                    related_entity_id=assignment.assignment_id,
                    related_entity_type='assignment'
                )
                db.session.add(notification)
            
            elif data['assignment_type'] == 'class':
                from app.models.class_enrollment import ClassEnrollment
                enrollments = ClassEnrollment.query.filter_by(
                    class_id=data['assigned_to_class'],
                    enrollment_status='active'
                ).all()
                
                for enrollment in enrollments:
                    notification = Notification(
                        recipient_id=enrollment.student_id,
                        sender_id=assigned_by,
                        notification_type='assignment',
                        title='Bài tập mới cho lớp',
                        content=f'Lớp có bài tập mới với video hướng dẫn',
                        related_entity_id=assignment.assignment_id,
                        related_entity_type='assignment'
                    )
                    db.session.add(notification)
            
            db.session.commit()
            return {'success': True, 'assignment': assignment}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    @staticmethod
    def get_assignments_by_instructor(instructor_id: int, filters: dict | None = None):
        query = Assignment.query.filter_by(assigned_by=instructor_id)
        if filters:
            assignment_type = filters.get('assignment_type')
            if assignment_type in ['individual', 'class']:
                query = query.filter_by(assignment_type=assignment_type)

            priority = filters.get('priority')
            if priority in ['low', 'normal', 'high', 'urgent']:
                query = query.filter_by(priority=priority)

            # status filter (pending/submitted/graded) requires joins/aggregation; skipping server-side for now
        return query.order_by(Assignment.created_at.desc()).all()

    @staticmethod
    def get_assignment_by_id(assignment_id: int):
        return Assignment.query.get(assignment_id)

    @staticmethod
    def get_assigned_students(assignment_id: int):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return []

        if assignment.assignment_type == 'individual':
            return [assignment.student] if assignment.student else []

        enrollments = ClassEnrollment.query.filter_by(
            class_id=assignment.assigned_to_class,
            enrollment_status='active',
        ).all()
        return [e.student for e in enrollments]

    @staticmethod
    def get_submission_status(assignment_id: int):
        students = AssignmentService.get_assigned_students(assignment_id)
        status_list = []
        for student in students:
            videos = TrainingVideo.query.filter_by(
                student_id=student.user_id,
                assignment_id=assignment_id,
            ).order_by(TrainingVideo.uploaded_at.desc()).all()
            
            latest_video = videos[0] if videos else None
            submitted = len(videos) > 0
            
            # Determine status
            if submitted and latest_video.manual_evaluations:
                status = 'graded'
                score = latest_video.manual_evaluations[0].overall_score
                submitted_at = latest_video.uploaded_at
            elif submitted:
                status = 'submitted'
                score = None
                submitted_at = latest_video.uploaded_at
            else:
                status = 'pending'
                score = None
                submitted_at = None
            
            status_list.append({
                'student': student,
                'status': status,
                'submitted': submitted,
                'video_count': len(videos),
                'latest_video': latest_video,
                'submitted_at': submitted_at,
                'score': score,
            })
        return status_list

    @staticmethod
    def update_assignment(assignment_id: int, data: dict, instructor_id: int):
        """Cập nhật assignment"""
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return {'success': False, 'message': 'Không tìm thấy bài tập'}
        if assignment.assigned_by != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền sửa bài tập này'}
        
        try:
            if 'routine_id' in data:
                assignment.routine_id = data['routine_id']
            if 'assignment_type' in data:
                assignment.assignment_type = data['assignment_type']
            if 'assigned_to_student' in data:
                assignment.assigned_to_student = data.get('assigned_to_student')
            if 'assigned_to_class' in data:
                assignment.assigned_to_class = data.get('assigned_to_class')
            if 'deadline' in data:
                assignment.deadline = data.get('deadline')
            if 'instructions' in data:
                assignment.instructions = data.get('instructions')
            if 'priority' in data:
                assignment.priority = data.get('priority', 'normal')
            if 'is_mandatory' in data:
                assignment.is_mandatory = data.get('is_mandatory', True)
            if 'instructor_video_url' in data and data['instructor_video_url']:
                assignment.instructor_video_url = data['instructor_video_url']
            if 'grading_method' in data:
                assignment.grading_method = data.get('grading_method', 'manual')
            
            db.session.commit()
            return {'success': True, 'assignment': assignment}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}

    @staticmethod
    def delete_assignment(assignment_id: int, instructor_id: int):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return {'success': False, 'message': 'Không tìm thấy bài tập'}
        if assignment.assigned_by != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa bài tập này'}
        db.session.delete(assignment)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_assignments_for_student(student_id: int):
        individual = Assignment.query.filter_by(
            assignment_type='individual',
            assigned_to_student=student_id,
        ).all()

        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active',
        ).all()
        class_ids = [e.class_id for e in enrollments]
        class_assignments = Assignment.query.filter(
            Assignment.assignment_type == 'class',
            Assignment.assigned_to_class.in_(class_ids),
        ).all() if class_ids else []
        return individual + class_assignments

    @staticmethod
    def can_submit(assignment_id: int, student_id: int):
        """Check if student can submit assignment"""
        assignment = Assignment.query.get(assignment_id)
        
        if not assignment:
            return {'can_submit': False, 'message': 'Bài tập không tồn tại'}
        
        # Check deadline
        if assignment.is_expired:
            return {'can_submit': False, 'message': 'Bài tập đã quá hạn nộp'}
        
        return {'can_submit': True}
    
    @staticmethod
    def get_active_assignments_for_student(student_id: int):
        """Get active assignments that haven't expired"""
        from datetime import datetime
        
        # Get individual assignments
        individual = Assignment.query.filter_by(
            assigned_to_student=student_id,
            assignment_type='individual'
        ).all()
        
        # Get class assignments
        from app.models.class_enrollment import ClassEnrollment
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        
        class_assignments = Assignment.query.filter(
            Assignment.assigned_to_class.in_(class_ids),
            Assignment.assignment_type == 'class'
        ).all() if class_ids else []
        
        all_assignments = individual + class_assignments
        
        # Filter out expired assignments
        active = [a for a in all_assignments if not a.is_expired]
        
        return active

    @staticmethod
    def get_active_class_assignments_for_student(student_id: int):
        """Get active class assignments (assigned via student's classes only)"""
        from app.models.class_enrollment import ClassEnrollment
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        if not class_ids:
            return []
        class_assignments = Assignment.query.filter(
            Assignment.assignment_type == 'class',
            Assignment.assigned_to_class.in_(class_ids)
        ).all()
        return [a for a in class_assignments if not a.is_expired]

    @staticmethod
    def get_form_prefill_data_for_class(class_id: int, instructor_id: int):
        """Get pre-fill data for assignment form when creating from class context"""
        if not class_id:
            return None
        
        class_obj = Class.query.get(class_id)
        if not class_obj or class_obj.instructor_id != instructor_id:
            return None
        
        return {
            'assignment_type': 'class',
            'assigned_to_class': class_id
        }

    @staticmethod
    def get_recent_class_assignments(class_id: int, limit: int = 5):
        """Get recent assignments for a class with stats"""
        assignments = Assignment.query.filter_by(
            assigned_to_class=class_id
        ).order_by(Assignment.created_at.desc()).limit(limit).all()
        
        assignment_stats = {}
        for assignment in assignments:
            status_list = AssignmentService.get_submission_status(assignment.assignment_id)
            total_students = len(status_list)
            graded = sum(1 for s in status_list if s['status'] == 'graded')
            submitted = sum(1 for s in status_list if s['status'] == 'submitted')
            pending = sum(1 for s in status_list if s['status'] == 'pending')
            assignment_stats[assignment.assignment_id] = {
                'total': total_students,
                'graded': graded,
                'submitted': submitted,
                'pending': pending
            }
        
        return {
            'assignments': assignments,
            'stats': assignment_stats
        }

    @staticmethod
    def get_assignments_with_stats(instructor_id: int, filters: dict = None):
        """Get assignments with stats for instructor"""
        assignments = AssignmentService.get_assignments_by_instructor(instructor_id, filters)
        
        assignment_stats = {}
        total_pending = 0
        total_submitted = 0
        total_graded = 0

        for assignment in assignments:
            status_list = AssignmentService.get_submission_status(assignment.assignment_id)
            total_students = len(status_list)
            pending = sum(1 for s in status_list if s['status'] == 'pending')
            submitted = sum(1 for s in status_list if s['status'] == 'submitted')
            graded = sum(1 for s in status_list if s['status'] == 'graded')

            total_pending += pending
            total_submitted += submitted
            total_graded += graded

            completion_percent = int((graded / total_students) * 100) if total_students else 0

            assignment_stats[assignment.assignment_id] = {
                'total_students': total_students,
                'pending': pending,
                'submitted': submitted,
                'graded': graded,
                'completion_percent': completion_percent,
            }

        stats = {
            'pending': total_pending,
            'submitted': total_submitted,
            'graded': total_graded,
        }

        return {
            'assignments': assignments,
            'assignment_stats': assignment_stats,
            'stats': stats
        }


