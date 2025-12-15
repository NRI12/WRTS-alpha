from app.models import db
from app.models.martial_routine import MartialRoutine
from app.models.weapon import Weapon
from datetime import datetime


class RoutineService:
    @staticmethod
    def get_all_weapons():
        return Weapon.query.filter_by(is_active=True).order_by(Weapon.display_order).all()

    @staticmethod
    def get_routines_by_instructor(instructor_id: int, filters=None):
        query = MartialRoutine.query.filter_by(instructor_id=instructor_id)

        if filters:
            if filters.get('level'):
                query = query.filter_by(level=filters['level'])
            if filters.get('weapon_id'):
                query = query.filter_by(weapon_id=filters['weapon_id'])
            if filters.get('is_published') is not None:
                query = query.filter_by(is_published=filters['is_published'])

        return query.order_by(MartialRoutine.created_at.desc()).all()

    @staticmethod
    def get_routine_by_id(routine_id: int):
        return MartialRoutine.query.get(routine_id)

    @staticmethod
    def create_routine(data: dict, instructor_id: int):
        if MartialRoutine.query.filter_by(routine_code=data['routine_code']).first():
            return {'success': False, 'message': 'Mã bài võ đã tồn tại'}

        routine = MartialRoutine(
            routine_code=data['routine_code'],
            routine_name=data['routine_name'],
            description=data.get('description'),
            weapon_id=data['weapon_id'],
            level=data['level'],
            difficulty_score=data.get('difficulty_score', 1.0),
            reference_video_url=data.get('reference_video_url'),
            thumbnail_url=data.get('thumbnail_url'),
            duration_seconds=data['duration_seconds'],
            total_moves=data.get('total_moves', 1),
            instructor_id=instructor_id,
            pass_threshold=data.get('pass_threshold', 70.00),
            is_published=False,
            is_active=True,
        )

        db.session.add(routine)
        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def update_routine(routine_id: int, data: dict, instructor_id: int):
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền sửa bài võ này'}

        routine.routine_name = data['routine_name']
        routine.description = data.get('description')
        routine.weapon_id = data['weapon_id']
        routine.level = data['level']
        routine.difficulty_score = data.get('difficulty_score', routine.difficulty_score)
        routine.reference_video_url = data.get('reference_video_url', routine.reference_video_url)
        routine.thumbnail_url = data.get('thumbnail_url', routine.thumbnail_url)
        routine.duration_seconds = data['duration_seconds']
        routine.total_moves = data.get('total_moves', routine.total_moves)
        routine.pass_threshold = data.get('pass_threshold', routine.pass_threshold)

        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def publish_routine(routine_id: int, instructor_id: int):
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}

        routine.is_published = True
        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def unpublish_routine(routine_id: int, instructor_id: int):
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}

        routine.is_published = False
        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def delete_routine(routine_id: int, instructor_id: int):
        from app.models.training_video import TrainingVideo

        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa bài võ này'}

        video_count = TrainingVideo.query.filter_by(routine_id=routine_id).count()
        if video_count > 0:
            return {'success': False, 'message': f'Không thể xóa - đã có {video_count} video bài tập'}

        db.session.delete(routine)
        db.session.commit()
        return {'success': True}

    # Evaluation criteria removed

    @staticmethod
    def get_published_routines(filters=None):
        query = MartialRoutine.query.filter_by(is_published=True, is_active=True)

        if filters:
            if filters.get('level'):
                query = query.filter_by(level=filters['level'])
            if filters.get('weapon_id'):
                query = query.filter_by(weapon_id=filters['weapon_id'])

        return query.order_by(MartialRoutine.created_at.desc()).all()

    @staticmethod
    def get_routines_for_student(student_id: int, filters=None):
        from app.models.assignment import Assignment
        from app.models.class_enrollment import ClassEnrollment
        from sqlalchemy import or_

        enrollments = ClassEnrollment.query.filter_by(student_id=student_id, enrollment_status='active').all()
        class_ids = [e.class_id for e in enrollments]

        routine_ids = set()
        # class assignments only (scope strictly to classes the student joined)
        if class_ids:
            class_assignments = Assignment.query.filter(Assignment.assignment_type=='class', Assignment.assigned_to_class.in_(class_ids)).all()
            routine_ids.update([a.routine_id for a in class_assignments])

        query = MartialRoutine.query.filter(MartialRoutine.is_active==True, MartialRoutine.is_published==True)
        if routine_ids:
            query = query.filter(MartialRoutine.routine_id.in_(list(routine_ids)))
        else:
            # no assignments, return empty list
            return []

        if filters:
            if filters.get('level'):
                query = query.filter_by(level=filters['level'])
            if filters.get('weapon_id'):
                query = query.filter_by(weapon_id=filters['weapon_id'])

        return query.order_by(MartialRoutine.created_at.desc()).all()


