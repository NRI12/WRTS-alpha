"""
System tests for complete end-to-end workflows
"""
import pytest
from datetime import datetime, timedelta
from werkzeug.datastructures import FileStorage
from io import BytesIO
from app.models.martial_routine import MartialRoutine
from app.models.weapon import Weapon
from app.models.assignment import Assignment
from app.models.training_video import TrainingVideo
from app.models.manual_evaluation import ManualEvaluation


class TestCompleteAssignmentLifecycle:
    """Test complete assignment workflow from creation to final grade"""

    def test_assignment_creation_submission_grading(self, client, db_session,
                                                     instructor_user, sample_user, seed_roles):
        """
        End-to-end test:
        1. Instructor creates routine with video
        2. Instructor creates assignment
        3. Student submits video
        4. AI processes video (mocked)
        5. Instructor grades manually
        6. Student views final grade
        """

        # Setup: Create a routine first
        weapon = Weapon(
            weapon_code='SWORD',
            weapon_name_vi='Kiếm',
            weapon_name_en='Sword',
            is_active=True,
            display_order=1
        )
        db_session.add(weapon)
        db_session.commit()

        routine = MartialRoutine(
            routine_name='Test Routine',
            routine_code='SYSTEM001',
            instructor_id=instructor_user.user_id,
            weapon_id=weapon.weapon_id,
            level='beginner',
            difficulty_score=5,
            reference_video_url='/static/uploads/test_video.mp4',
            duration_seconds=60,
            total_moves=10,
            is_published=True,
            is_active=True,
            pass_threshold=70.0
        )
        db_session.add(routine)
        db_session.commit()

        # Step 1: Instructor creates assignment
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        assignment_data = {
            'routine_id': routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'grading_method': 'both',  # AI + Manual
            'instructor_video_url': '/static/uploads/instructor_demo.mp4',
            'deadline': (datetime.now() + timedelta(days=7)).isoformat()
        }

        response = client.post('/instructor/assignments/create',
                              data=assignment_data, follow_redirects=True)
        assert response.status_code == 200

        assignment = Assignment.query.filter_by(routine_id=routine.routine_id).first()
        assert assignment is not None

        # Step 2: Student submits video
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'test_student',
            'password': 'password123'
        })

        # Create mock video file
        video_data = BytesIO(b'fake video content')
        video_file = FileStorage(
            stream=video_data,
            filename='student_submission.mp4',
            content_type='video/mp4'
        )

        response = client.post(f'/student/assignments/{assignment.assignment_id}/submit',
                              data={'video': video_file},
                              content_type='multipart/form-data',
                              follow_redirects=True)
        assert response.status_code in [200, 302]

        # Verify video was uploaded
        video = TrainingVideo.query.filter_by(
            assignment_id=assignment.assignment_id,
            student_id=sample_user.user_id
        ).first()
        assert video is not None

        # Step 3: Instructor grades
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        evaluation_data = {
            'overall_score': 85,
            'technique_score': 80,
            'posture_score': 85,
            'spirit_score': 90,
            'comments': 'Good performance',
            'is_passed': True
        }

        response = client.post(f'/instructor/videos/{video.video_id}/evaluate',
                              data=evaluation_data, follow_redirects=True)
        assert response.status_code == 200

        # Step 4: Verify evaluation exists
        evaluation = ManualEvaluation.query.filter_by(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id
        ).first()
        assert evaluation is not None
        assert evaluation.overall_score == 85

        # Step 5: Student views grade
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'test_student',
            'password': 'password123'
        })

        response = client.get(f'/student/videos/{video.video_id}')
        assert response.status_code == 200
        assert b'85' in response.data  # Score should be visible


class TestCompleteClassLifecycle:
    """Test complete class lifecycle workflow"""

    def test_class_proposal_to_completion(self, client, db_session, instructor_user,
                                         manager_user, sample_user):
        """Test complete class lifecycle: propose -> approve -> schedule -> complete"""
        from app.models.class_model import Class
        from app.models.class_enrollment import ClassEnrollment

        # Step 1: Instructor proposes class
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        class_data = {
            'class_code': 'LIFECYCLE001',
            'class_name': 'Lifecycle Test Class',
            'description': 'Test class lifecycle',
            'level': 'beginner',
            'max_students': 20,
            'start_date': datetime.now().date().isoformat()
        }

        response = client.post('/instructor/propose-class', data=class_data, follow_redirects=True)
        assert response.status_code == 200

        pending_class = Class.query.filter_by(class_code='LIFECYCLE001').first()
        assert pending_class is not None
        assert pending_class.approval_status == 'pending'

        # Step 2: Manager approves
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'manager_test',
            'password': 'password123'
        })

        response = client.post(f'/manager/classes/{pending_class.class_id}/review',
                              data={'decision': 'approve'}, follow_redirects=True)
        assert response.status_code == 200

        db_session.refresh(pending_class)
        assert pending_class.approval_status == 'approved'

        # Step 3: Student enrolls
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'test_student',
            'password': 'password123'
        })

        response = client.post(f'/student/classes/{pending_class.class_id}/enroll',
                              follow_redirects=True)
        assert response.status_code == 200

        enrollment = ClassEnrollment.query.filter_by(
            class_id=pending_class.class_id,
            student_id=sample_user.user_id
        ).first()
        assert enrollment is not None

        # Step 4: Complete enrollment
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        from app.services.class_service import ClassService
        result = ClassService.update_enrollment_status(
            enrollment.enrollment_id,
            'completed'
        )

        assert result['success'] == True
        db_session.refresh(enrollment)
        assert enrollment.enrollment_status == 'completed'


class TestSecurityWorkflow:
    """Test security and authorization workflows"""

    def test_unauthorized_access_attempts(self, client, db_session, sample_user, instructor_user):
        """Test unauthorized access to protected resources"""
        # Student tries to access instructor routes
        client.post('/auth/login', data={
            'username': 'test_student',
            'password': 'password123'
        })

        # Try to access instructor dashboard
        response = client.get('/instructor/dashboard', follow_redirects=False)
        # Should redirect or show error
        assert response.status_code in [302, 403]

        # Try to create assignment (should fail)
        response = client.post('/instructor/assignments/create',
                              data={}, follow_redirects=False)
        assert response.status_code in [302, 403, 400]

    def test_cross_user_data_access(self, client, db_session, sample_user, instructor_user, seed_roles):
        """Test users cannot access other users' data"""
        from app.models.user import User
        from app.models.role import Role

        # Create another student
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        other_student = User(
            username='other_student',
            email='other@test.com',
            full_name='Other Student',
            role_id=student_role.role_id,
            is_active=True
        )
        other_student.set_password('password123')
        db_session.add(other_student)
        db_session.commit()

        # Create assignment for sample_user
        from app.models.assignment import Assignment
        from app.models.martial_routine import MartialRoutine
        from app.models.weapon import Weapon

        weapon = Weapon(weapon_code='SWORD2', weapon_name_vi='Kiếm', weapon_name_en='Sword', is_active=True, display_order=1)
        db_session.add(weapon)
        db_session.commit()

        routine = MartialRoutine(
            routine_code='SEC001',
            routine_name='Security Test',
            instructor_id=instructor_user.user_id,
            weapon_id=weapon.weapon_id,
            level='beginner',
            duration_seconds=60,
            is_published=True,
            is_active=True
        )
        db_session.add(routine)
        db_session.commit()

        assignment = Assignment(
            routine_id=routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='individual',
            assigned_to_student=sample_user.user_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.commit()

        # Other student tries to access sample_user's assignment
        client.post('/auth/login', data={
            'username': 'other_student',
            'password': 'password123'
        })

        response = client.get(f'/student/assignments/{assignment.assignment_id}', follow_redirects=False)
        # Should not be accessible (redirect or 404)
        assert response.status_code in [302, 404, 403]

