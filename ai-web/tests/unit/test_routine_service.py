"""
Unit tests for RoutineService
"""
import pytest
from app.services.routine_service import RoutineService
from app.models.martial_routine import MartialRoutine
from app.models.weapon import Weapon
from app.models.training_video import TrainingVideo


class TestRoutineService:
    """Test RoutineService methods"""

    def test_get_all_weapons(self, db_session, sample_weapon):
        """Test getting all active weapons"""
        weapons = RoutineService.get_all_weapons()

        assert len(weapons) >= 1
        assert sample_weapon in weapons

    def test_create_routine_success(self, db_session, instructor_user, sample_weapon):
        """Test creating a routine"""
        data = {
            'routine_code': 'ROUTINE002',
            'routine_name': 'New Routine',
            'description': 'Test routine',
            'weapon_id': sample_weapon.weapon_id,
            'level': 'beginner',
            'difficulty_score': 5.0,
            'reference_video_url': '/static/uploads/routine.mp4',
            'duration_seconds': 90,
            'total_moves': 15,
            'pass_threshold': 75.0
        }

        result = RoutineService.create_routine(data, instructor_user.user_id)

        assert result['success'] == True
        assert result['routine'].routine_code == 'ROUTINE002'
        assert result['routine'].is_published == False

    def test_create_routine_duplicate_code(self, db_session, instructor_user, sample_routine):
        """Test creating routine with duplicate code fails"""
        data = {
            'routine_code': 'ROUTINE001',  # Already exists
            'routine_name': 'Another Routine',
            'weapon_id': sample_routine.weapon_id,
            'level': 'beginner',
            'duration_seconds': 60
        }

        result = RoutineService.create_routine(data, instructor_user.user_id)

        assert result['success'] == False
        assert 'mã bài võ' in result['message'].lower() or 'code' in result['message'].lower()

    def test_get_routine_by_id(self, db_session, sample_routine):
        """Test getting routine by ID"""
        routine = RoutineService.get_routine_by_id(sample_routine.routine_id)

        assert routine is not None
        assert routine.routine_code == 'ROUTINE001'

    def test_get_routine_by_id_not_found(self, db_session):
        """Test getting non-existent routine returns None"""
        routine = RoutineService.get_routine_by_id(99999)

        assert routine is None

    def test_get_routines_by_instructor(self, db_session, instructor_user, sample_routine):
        """Test getting routines by instructor"""
        routines = RoutineService.get_routines_by_instructor(instructor_user.user_id)

        assert len(routines) >= 1
        assert sample_routine in routines

    def test_get_routines_by_instructor_with_filters(self, db_session, instructor_user, sample_routine):
        """Test getting routines by instructor with filters"""
        # Filter by level
        routines = RoutineService.get_routines_by_instructor(
            instructor_user.user_id,
            filters={'level': 'beginner'}
        )

        assert len(routines) >= 1
        assert all(r.level == 'beginner' for r in routines)

        # Filter by weapon
        routines = RoutineService.get_routines_by_instructor(
            instructor_user.user_id,
            filters={'weapon_id': sample_routine.weapon_id}
        )

        assert len(routines) >= 1
        assert all(r.weapon_id == sample_routine.weapon_id for r in routines)

    def test_update_routine_success(self, db_session, sample_routine):
        """Test updating routine"""
        data = {
            'routine_name': 'Updated Routine Name',
            'description': 'Updated description',
            'weapon_id': sample_routine.weapon_id,
            'level': 'intermediate',
            'difficulty_score': 7.0,
            'duration_seconds': 120,
            'total_moves': 20,
            'pass_threshold': 80.0
        }

        result = RoutineService.update_routine(
            sample_routine.routine_id,
            data,
            sample_routine.instructor_id
        )

        assert result['success'] == True
        updated = MartialRoutine.query.get(sample_routine.routine_id)
        assert updated.routine_name == 'Updated Routine Name'
        assert updated.level == 'intermediate'

    def test_update_routine_not_found(self, db_session, instructor_user, sample_weapon):
        """Test updating non-existent routine fails"""
        data = {
            'routine_name': 'Updated',
            'weapon_id': sample_weapon.weapon_id,
            'level': 'beginner',
            'duration_seconds': 60
        }

        result = RoutineService.update_routine(99999, data, instructor_user.user_id)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower()

    def test_update_routine_unauthorized(self, db_session, sample_routine, instructor_user, seed_roles):
        """Test updating routine by non-owner fails"""
        # Create another instructor
        from app.models.user import User
        from app.models.role import Role
        instructor_role = Role.query.filter_by(role_code='INSTRUCTOR').first()
        other_instructor = User(
            username='other_instructor',
            email='other@test.com',
            full_name='Other Instructor',
            role_id=instructor_role.role_id,
            is_active=True
        )
        other_instructor.set_password('password123')
        db_session.add(other_instructor)
        db_session.commit()

        data = {
            'routine_name': 'Hacked Name',
            'weapon_id': sample_routine.weapon_id,
            'level': 'beginner',
            'duration_seconds': 60
        }

        result = RoutineService.update_routine(
            sample_routine.routine_id,
            data,
            other_instructor.user_id
        )

        assert result['success'] == False
        assert 'quyền' in result['message'].lower() or 'permission' in result['message'].lower()

    def test_publish_routine_success(self, db_session, instructor_user, sample_weapon):
        """Test publishing routine"""
        # Create unpublished routine
        data = {
            'routine_code': 'UNPUBLISHED001',
            'routine_name': 'Unpublished Routine',
            'weapon_id': sample_weapon.weapon_id,
            'level': 'beginner',
            'duration_seconds': 60
        }
        create_result = RoutineService.create_routine(data, instructor_user.user_id)
        routine_id = create_result['routine'].routine_id

        result = RoutineService.publish_routine(routine_id, instructor_user.user_id)

        assert result['success'] == True
        routine = MartialRoutine.query.get(routine_id)
        assert routine.is_published == True

    def test_publish_routine_not_found(self, db_session, instructor_user):
        """Test publishing non-existent routine fails"""
        result = RoutineService.publish_routine(99999, instructor_user.user_id)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower()

    def test_unpublish_routine_success(self, db_session, sample_routine):
        """Test unpublishing routine"""
        # Ensure it's published first
        sample_routine.is_published = True
        db_session.commit()

        result = RoutineService.unpublish_routine(
            sample_routine.routine_id,
            sample_routine.instructor_id
        )

        assert result['success'] == True
        routine = MartialRoutine.query.get(sample_routine.routine_id)
        assert routine.is_published == False

    def test_delete_routine_success(self, db_session, instructor_user, sample_weapon):
        """Test deleting routine without videos"""
        # Create a routine
        data = {
            'routine_code': 'DELETE001',
            'routine_name': 'To Delete',
            'weapon_id': sample_weapon.weapon_id,
            'level': 'beginner',
            'duration_seconds': 60
        }
        create_result = RoutineService.create_routine(data, instructor_user.user_id)
        routine_id = create_result['routine'].routine_id

        result = RoutineService.delete_routine(routine_id, instructor_user.user_id)

        assert result['success'] == True
        assert MartialRoutine.query.get(routine_id) is None

    def test_delete_routine_with_videos_fails(self, db_session, sample_routine, sample_user):
        """Test deleting routine with videos fails"""
        # Create a video for this routine
        from app.models.assignment import Assignment
        from app.models.training_video import TrainingVideo

        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=sample_routine.instructor_id,
            assignment_type='individual',
            assigned_to_student=sample_user.user_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/video.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.commit()

        result = RoutineService.delete_routine(
            sample_routine.routine_id,
            sample_routine.instructor_id
        )

        assert result['success'] == False
        assert 'video' in result['message'].lower() or 'bài tập' in result['message'].lower()

    def test_get_published_routines(self, db_session, sample_routine):
        """Test getting published routines"""
        routines = RoutineService.get_published_routines()

        assert len(routines) >= 1
        assert sample_routine in routines
        assert all(r.is_published == True for r in routines)

    def test_get_published_routines_with_filters(self, db_session, sample_routine):
        """Test getting published routines with filters"""
        routines = RoutineService.get_published_routines(filters={'level': 'beginner'})

        assert len(routines) >= 1
        assert all(r.level == 'beginner' for r in routines)

