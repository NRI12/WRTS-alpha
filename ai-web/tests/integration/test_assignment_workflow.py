"""
Integration tests for assignment workflow
"""
import pytest
from datetime import datetime, timedelta
from werkzeug.datastructures import FileStorage
from io import BytesIO
from app.models.assignment import Assignment
from app.models.training_video import TrainingVideo
from app.models.manual_evaluation import ManualEvaluation


class TestAssignmentWorkflow:
    """Test complete assignment workflows"""

    def test_assignment_creation_and_submission(self, client, db_session, instructor_user,
                                                sample_user, sample_routine):
        """Test creating assignment and student submission"""
        # Instructor logs in
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        # Create assignment
        assignment_data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'individual',
            'assigned_to_student': sample_user.user_id,
            'deadline': (datetime.now() + timedelta(days=7)).isoformat(),
            'instructions': 'Complete this routine',
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }

        response = client.post('/instructor/assignments/create',
                              data=assignment_data, follow_redirects=True)
        assert response.status_code == 200

        assignment = Assignment.query.filter_by(
            routine_id=sample_routine.routine_id,
            assigned_to_student=sample_user.user_id
        ).first()
        assert assignment is not None

        # Student logs in and submits video
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

        # Should succeed (status 200) or redirect
        assert response.status_code in [200, 302]

        # Verify video was uploaded
        video = TrainingVideo.query.filter_by(
            assignment_id=assignment.assignment_id,
            student_id=sample_user.user_id
        ).first()
        assert video is not None

    def test_assignment_grading_workflow(self, client, db_session, instructor_user,
                                        sample_user, sample_routine):
        """Test complete assignment grading workflow"""
        # Create assignment
        assignment = Assignment(
            routine_id=sample_routine.routine_id,
            assigned_by=instructor_user.user_id,
            assignment_type='individual',
            assigned_to_student=sample_user.user_id,
            instructor_video_url='/static/uploads/demo.mp4',
            grading_method='manual'
        )
        db_session.add(assignment)
        db_session.flush()

        # Create video submission
        video = TrainingVideo(
            student_id=sample_user.user_id,
            assignment_id=assignment.assignment_id,
            routine_id=sample_routine.routine_id,
            video_url='/static/uploads/submission.mp4',
            processing_status='completed'
        )
        db_session.add(video)
        db_session.commit()

        # Instructor logs in and grades
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

        # Verify evaluation exists
        evaluation = ManualEvaluation.query.filter_by(
            video_id=video.video_id,
            instructor_id=instructor_user.user_id
        ).first()
        assert evaluation is not None
        assert evaluation.overall_score == 85

        # Student views grade
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'test_student',
            'password': 'password123'
        })

        response = client.get(f'/student/videos/{video.video_id}')
        assert response.status_code == 200
        assert b'85' in response.data  # Score should be visible

    def test_class_assignment_notification(self, client, db_session, instructor_user,
                                          approved_class, sample_user, sample_routine):
        """Test class assignment sends notifications to all enrolled students"""
        from app.models.class_enrollment import ClassEnrollment
        from app.models.notification import Notification

        # Enroll student
        from app.services.class_service import ClassService
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        # Instructor logs in
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        # Create class assignment
        assignment_data = {
            'routine_id': sample_routine.routine_id,
            'assignment_type': 'class',
            'assigned_to_class': approved_class.class_id,
            'deadline': (datetime.now() + timedelta(days=7)).isoformat(),
            'instructor_video_url': '/static/uploads/demo.mp4',
            'grading_method': 'manual'
        }

        response = client.post('/instructor/assignments/create',
                              data=assignment_data, follow_redirects=True)
        assert response.status_code == 200

        # Verify notification was created
        assignment = Assignment.query.filter_by(
            assigned_to_class=approved_class.class_id
        ).first()

        notifications = Notification.query.filter_by(
            notification_type='assignment',
            related_entity_id=assignment.assignment_id
        ).all()

        assert len(notifications) >= 1
        assert any(n.recipient_id == sample_user.user_id for n in notifications)

