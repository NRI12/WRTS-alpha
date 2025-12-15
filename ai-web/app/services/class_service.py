from datetime import datetime
from app.models import db
from app.models.class_model import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.user import User
from app.models.role import Role
from app.utils.helpers import get_vietnam_time


class ClassService:
    @staticmethod
    def create_class_proposal(data: dict, instructor_id: int):
        if Class.query.filter_by(class_code=data['class_code']).first():
            return {'success': False, 'message': 'Mã lớp đã tồn tại'}

        new_class = Class(
            class_code=data['class_code'],
            class_name=data['class_name'],
            description=data.get('description'),
            instructor_id=instructor_id,
            level=data['level'],
            max_students=data['max_students'],
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            approval_status='pending',
            is_active=False,
        )

        db.session.add(new_class)
        db.session.commit()
        return {'success': True, 'class': new_class}

    @staticmethod
    def get_pending_proposals():
        return Class.query.filter_by(approval_status='pending').order_by(Class.created_at.desc()).all()

    @staticmethod
    def get_approved_classes_by_instructor(instructor_id: int):
        return Class.query.filter_by(instructor_id=instructor_id, approval_status='approved').all()

    @staticmethod
    def get_my_proposals(instructor_id: int):
        return Class.query.filter_by(instructor_id=instructor_id).order_by(Class.created_at.desc()).all()

    @staticmethod
    def approve_class(class_id: int, manager_id: int):
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return {'success': False, 'message': 'Không tìm thấy lớp học'}
        if class_obj.approval_status != 'pending':
            return {'success': False, 'message': 'Lớp này đã được xử lý'}

        class_obj.approval_status = 'approved'
        class_obj.approved_by = manager_id
        class_obj.approved_at = get_vietnam_time()
        class_obj.is_active = True

        db.session.commit()
        return {'success': True, 'class': class_obj}

    @staticmethod
    def reject_class(class_id: int, manager_id: int, reason: str):
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return {'success': False, 'message': 'Không tìm thấy lớp học'}
        if class_obj.approval_status != 'pending':
            return {'success': False, 'message': 'Lớp này đã được xử lý'}

        class_obj.approval_status = 'rejected'
        class_obj.approved_by = manager_id
        class_obj.approved_at = get_vietnam_time()
        class_obj.rejection_reason = reason
        class_obj.is_active = False

        db.session.commit()
        return {'success': True, 'class': class_obj}
    @staticmethod
    def get_all_classes():
        return Class.query.all()

    @staticmethod
    def get_classes_by_instructor(instructor_id: int):
        return Class.query.filter_by(instructor_id=instructor_id).all()

    @staticmethod
    def get_class_by_id(class_id: int):
        return Class.query.get(class_id)

    @staticmethod
    def create_class(data: dict, instructor_id: int):
        if Class.query.filter_by(class_code=data['class_code']).first():
            return {'success': False, 'message': 'Mã lớp đã tồn tại'}

        new_class = Class(
            class_code=data['class_code'],
            class_name=data['class_name'],
            description=data.get('description'),
            instructor_id=instructor_id,
            level=data['level'],
            max_students=data['max_students'],
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            is_active=True,
        )

        db.session.add(new_class)
        db.session.commit()
        return {'success': True, 'class': new_class}

    @staticmethod
    def update_class(class_id: int, data: dict):
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return {'success': False, 'message': 'Không tìm thấy lớp học'}

        class_obj.class_name = data['class_name']
        class_obj.description = data.get('description')
        class_obj.level = data['level']
        class_obj.max_students = data['max_students']
        class_obj.end_date = data.get('end_date')
        class_obj.is_active = data.get('is_active', True)

        db.session.commit()
        return {'success': True, 'class': class_obj}

    @staticmethod
    def delete_class(class_id: int):
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return {'success': False, 'message': 'Không tìm thấy lớp học'}

        db.session.delete(class_obj)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_enrolled_students(class_id: int):
        return ClassEnrollment.query.filter_by(class_id=class_id).all()

    @staticmethod
    def get_available_students(class_id: int):
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        if not student_role:
            return []

        all_students = User.query.filter_by(role_id=student_role.role_id, is_active=True).all()
        enrolled_ids = [e.student_id for e in ClassEnrollment.query.filter_by(class_id=class_id).all()]
        return [s for s in all_students if s.user_id not in enrolled_ids]

    @staticmethod
    def enroll_student(class_id: int, student_id: int, notes: str | None = None):
        from app.models.class_schedule import ClassSchedule
        
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return {'success': False, 'message': 'Không tìm thấy lớp học'}

        student = User.query.get(student_id)
        if not student:
            return {'success': False, 'message': 'Không tìm thấy học viên'}

        existing = ClassEnrollment.query.filter_by(class_id=class_id, student_id=student_id).first()
        if existing:
            return {'success': False, 'message': 'Học viên đã đăng ký lớp này'}

        if class_obj.current_students >= class_obj.max_students:
            return {'success': False, 'message': 'Lớp đã đầy'}

        new_schedules = ClassSchedule.query.filter_by(
            class_id=class_id,
            is_active=True
        ).all()
        
        if new_schedules:
            # Lấy tất cả lớp học sinh đang học
            student_enrollments = ClassEnrollment.query.filter_by(
                student_id=student_id,
                enrollment_status='active'
            ).all()
            
            student_class_ids = [e.class_id for e in student_enrollments]
            
            if student_class_ids:
                # Lấy tất cả lịch học của các lớp đang học
                existing_schedules = ClassSchedule.query.filter(
                    ClassSchedule.class_id.in_(student_class_ids),
                    ClassSchedule.is_active == True
                ).all()
                
                # Kiểm tra conflict
                for new_sch in new_schedules:
                    for exist_sch in existing_schedules:
                        # Kiểm tra cùng ngày
                        if new_sch.day_of_week == exist_sch.day_of_week:
                            # Kiểm tra trùng giờ
                            if (new_sch.time_start < exist_sch.time_end and 
                                new_sch.time_end > exist_sch.time_start):
                                
                                days_map = {
                                    'monday': 'Thứ 2', 'tuesday': 'Thứ 3', 
                                    'wednesday': 'Thứ 4', 'thursday': 'Thứ 5',
                                    'friday': 'Thứ 6', 'saturday': 'Thứ 7', 
                                    'sunday': 'Chủ nhật'
                                }
                                day_vn = days_map.get(exist_sch.day_of_week, exist_sch.day_of_week)
                                
                                conflict_class = Class.query.get(exist_sch.class_id)
                                conflict_msg = (
                                    f'Học sinh đã có lịch học vào {day_vn} '
                                    f'{exist_sch.time_start.strftime("%H:%M")}-'
                                    f'{exist_sch.time_end.strftime("%H:%M")} '
                                    f'(Lớp: {conflict_class.class_name})'
                                )
                                return {'success': False, 'message': conflict_msg}

        # Nếu không trùng lịch → cho phép enroll
        enrollment = ClassEnrollment(
            class_id=class_id,
            student_id=student_id,
            enrollment_status='active',
            notes=notes,
        )

        db.session.add(enrollment)
        db.session.commit()
        return {'success': True, 'enrollment': enrollment}
    @staticmethod
    def remove_student(enrollment_id: int):
        enrollment = ClassEnrollment.query.get(enrollment_id)
        if not enrollment:
            return {'success': False, 'message': 'Không tìm thấy đăng ký'}

        db.session.delete(enrollment)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def update_enrollment_status(enrollment_id: int, status: str):
        enrollment = ClassEnrollment.query.get(enrollment_id)
        if not enrollment:
            return {'success': False, 'message': 'Không tìm thấy đăng ký'}

        enrollment.enrollment_status = status
        if status == 'completed':
            enrollment.completed_at = get_vietnam_time()

        db.session.commit()
        return {'success': True, 'enrollment': enrollment}

    @staticmethod
    def get_statistics():
        total_classes = Class.query.count()
        active_classes = Class.query.filter_by(is_active=True).count()
        total_enrollments = ClassEnrollment.query.filter_by(enrollment_status='active').count()

        beginner_classes = Class.query.filter_by(level='beginner', is_active=True).count()
        intermediate_classes = Class.query.filter_by(level='intermediate', is_active=True).count()
        advanced_classes = Class.query.filter_by(level='advanced', is_active=True).count()

        student_role = Role.query.filter_by(role_code='STUDENT').first()
        total_students = (
            User.query.filter_by(role_id=student_role.role_id, is_active=True).count() if student_role else 0
        )

        return {
            'total_classes': total_classes,
            'active_classes': active_classes,
            'total_enrollments': total_enrollments,
            'beginner_classes': beginner_classes,
            'intermediate_classes': intermediate_classes,
            'advanced_classes': advanced_classes,
            'total_students': total_students,
        }

    @staticmethod
    def format_schedule(class_obj):
        if hasattr(class_obj, 'schedules') and class_obj.schedules:
            from app.services.schedule_service import ScheduleService
            return ScheduleService.format_schedules(class_obj.schedules)
        
        return "Chưa có lịch học"