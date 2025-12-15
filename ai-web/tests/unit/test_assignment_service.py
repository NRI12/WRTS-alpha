"""
Unit tests for AssignmentService
"""
import pytest
from datetime import datetime, timedelta
from app.services.assignment_service import AssignmentService
from app.models.assignment import Assignment
from app.models.training_video import TrainingVideo
from app.models.class_enrollment import ClassEnrollment


class TestAssignmentService:
    """Test AssignmentService methods"""

    def test_create_assignment_individual_success(self, db_session, instructor_user, sample_routine, sample_user):
        """Test creating individual assignment"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'deadline': (datetime.now() + timedelta(days=7)),
            'instructions': 'Complete this routine',
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }

        result = AssignmentService.create_assignment(data, instructor_user.user_id)

        assert result['success'] == True
        assert result['assignment'].assignment_type == 'individual'
        assert result['assignment'].assigned_to_student == sample_user.user_id
        assert result['assignment'].instructor_video_url == '/static/uploads/demo.mp4'

    def test_create_assignment_class_success(self, db_session, instructor_user, sample_routine, approved_class):
        """Test creating class assignment"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'class',
            'assigned_to_class': approved_class.class_id,
            'deadline': (datetime.now() + timedelta(days=7)),
            'instructions': 'Class assignment',
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'both'
        }

        result = AssignmentService.create_assignment(data, instructor_user.user_id)

        assert result['success'] == True
        assert result['assignment'].assignment_type == 'class'
        assert result['assignment'].assigned_to_class == approved_class.class_id

    def test_create_assignment_missing_video_fails(self, db_session, instructor_user, sample_routine, sample_user):
        """Test creating assignment without instructor video fails"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'deadline': (datetime.now() + timedelta(days=7)),
            'grading_method': 'manual'
            # Missing instructor_video_url
        }

        result = AssignmentService.create_assignment(data, instructor_user.user_id)

        assert result['success'] == False
        assert 'video' in result['message'].lower()

    def test_create_assignment_unapproved_class_fails(self, db_session, instructor_user, sample_routine, pending_class):
        """Test creating assignment for unapproved class fails"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'class',
            'assigned_to_class': pending_class.class_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }

        result = AssignmentService.create_assignment(data, instructor_user.user_id)

        assert result['success'] == False
        assert 'duyệt' in result['message'].lower() or 'approved' in result['message'].lower()

    def test_create_assignment_wrong_instructor_fails(self, db_session, sample_routine, approved_class, seed_roles):
        """Test creating assignment for class by non-instructor fails"""
        from app.models.user import User
        from app.models.role import Role

        # Create another instructor
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
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'class',
            'assigned_to_class': approved_class.class_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }

        result = AssignmentService.create_assignment(data, other_instructor.user_id)

        assert result['success'] == False
        assert 'quyền' in result['message'].lower() or 'permission' in result['message'].lower()

    def test_get_assignment_by_id(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting assignment by ID"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        assignment = AssignmentService.get_assignment_by_id(assignment_id)

        assert assignment is not None
        assert assignment.assignment_type == 'individual'

    def test_get_assignments_by_instructor(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting assignments by instructor"""
        # Create multiple assignments
        for i in range(3):
            data = {
                'routine_id': sample_routine.routine_id,
                'assignment_type': 'individual',
                'assigned_to_student': sample_user.user_id,
                'instructor_video_url': f'/static/uploads/demo{i}.mp4',
                'grading_method': 'manual'
            }
            AssignmentService.create_assignment(data, instructor_user.user_id)

        assignments = AssignmentService.get_assignments_by_instructor(instructor_user.user_id)

        assert len(assignments) >= 3

    def test_get_assignments_by_instructor_with_filters(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting assignments by instructor with filters"""
        # Create assignments with different types
        data1 = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo1.mp4',
            'grading_method': 'manual'
        }
        AssignmentService.create_assignment(data1, instructor_user.user_id)

        assignments = AssignmentService.get_assignments_by_instructor(
            instructor_user.user_id,
            filters={'assignment_type': 'individual'}
        )

        assert len(assignments) >= 1
        assert all(a.assignment_type == 'individual' for a in assignments)

    def test_get_assigned_students_individual(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting assigned students for individual assignment"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        students = AssignmentService.get_assigned_students(assignment_id)

        assert len(students) == 1
        assert sample_user in students

    def test_get_assigned_students_class(self, db_session, instructor_user, sample_routine, approved_class, sample_user):
        """Test getting assigned students for class assignment"""
        # Enroll student in class
        from app.services.class_service import ClassService
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'class',
            'assigned_to_class': approved_class.class_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        students = AssignmentService.get_assigned_students(assignment_id)

        assert len(students) >= 1
        assert sample_user in students

    def test_get_submission_status(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting submission status"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        status_list = AssignmentService.get_submission_status(assignment_id)

        assert len(status_list) == 1
        assert status_list[0]['student'].user_id == sample_user.user_id
        assert status_list[0]['status'] == 'pending'

    def test_get_submission_status_with_video(self, db_session, instructor_user, sample_routine, sample_user):
        """Test getting submission status with submitted video"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        # Create a video submission
        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/submission.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.commit()

        status_list = AssignmentService.get_submission_status(assignment_id)

        assert len(status_list) == 1
        assert status_list[0]['status'] == 'submitted'
        assert status_list[0]['submitted'] == True

    def test_get_assignments_for_student(self, db_session, instructor_user, sample_routine, sample_user, approved_class):
        """Test getting assignments for student"""
        # Create individual assignment
        data1 = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo1.mp4',
            'grading_method': 'manual'
        }
        AssignmentService.create_assignment(data1, instructor_user.user_id)

        # Enroll in class and create class assignment
        from app.services.class_service import ClassService
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        data2 = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'class',
            'assigned_to_class': approved_class.class_id,
            'instructor_video_url': '/static/uploads/demo2.mp4',
            'grading_method': 'manual'
        }
        AssignmentService.create_assignment(data2, instructor_user.user_id)

        assignments = AssignmentService.get_assignments_for_student(sample_user.user_id)

        assert len(assignments) >= 2

    def test_can_submit_not_expired(self, db_session, instructor_user, sample_routine, sample_user):
        """Test can submit when assignment not expired"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'deadline': (datetime.now() + timedelta(days=7)),
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        result = AssignmentService.can_submit(assignment_id, sample_user.user_id)

        assert result['can_submit'] == True

    def test_can_submit_expired(self, db_session, instructor_user, sample_routine, sample_user):
        """Test cannot submit when assignment expired"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'deadline': (datetime.now() - timedelta(days=1)),  # Past deadline
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        result = AssignmentService.can_submit(assignment_id, sample_user.user_id)

        assert result['can_submit'] == False
        assert 'hạn' in result['message'].lower() or 'deadline' in result['message'].lower()

    def test_delete_assignment_success(self, db_session, instructor_user, sample_routine, sample_user):
        """Test deleting assignment"""
        data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        result = AssignmentService.delete_assignment(assignment_id, instructor_user.user_id)

        assert result['success'] == True
        assert Assignment.query.get(assignment_id) is None

    def test_delete_assignment_unauthorized(self, db_session, instructor_user, sample_routine, sample_user, seed_roles):
        """Test deleting assignment by non-creator fails"""
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
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }
        create_result = AssignmentService.create_assignment(data, instructor_user.user_id)
        assignment_id = create_result['assignment'].assignment_id

        result = AssignmentService.delete_assignment(assignment_id, other_instructor.user_id)

        assert result['success'] == False
        assert 'quyền' in result['message'].lower() or 'permission' in result['message'].lower()

