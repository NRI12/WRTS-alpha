"""
Integration tests for class management workflows
"""
import pytest
from datetime import datetime, timedelta
from app.models.class_model import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.user import User
from app.models.role import Role


class TestClassWorkflow:
    """Test complete class management workflows"""

    def test_class_proposal_approval_enrollment_flow(self, client, db_session,
                                                      instructor_user, manager_user, sample_user):
        """Test complete flow: propose -> approve -> enroll"""

        # Step 1: Instructor logs in and proposes class
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        class_data = {
            'class_code': 'INTEGRATION001',
            'class_name': 'Integration Test Class',
            'description': 'Test class for integration',
            'level': 'beginner',
            'max_students': 20,
            'start_date': datetime.now().date().isoformat()
        }

        response = client.post('/instructor/propose-class', data=class_data, follow_redirects=True)
        assert response.status_code == 200

        # Verify class is pending
        pending_class = Class.query.filter_by(class_code='INTEGRATION001').first()
        assert pending_class is not None
        assert pending_class.approval_status == 'pending'

        # Step 2: Manager logs in and approves class
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'manager_test',
            'password': 'password123'
        })

        response = client.post(f'/manager/classes/{pending_class.class_id}/review',
                              data={'decision': 'approve'}, follow_redirects=True)
        assert response.status_code == 200

        # Verify class is approved
        db_session.refresh(pending_class)
        assert pending_class.approval_status == 'approved'

        # Step 3: Student enrolls in approved class
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'test_student',
            'password': 'password123'
        })

        response = client.post(f'/student/classes/{pending_class.class_id}/enroll',
                              follow_redirects=True)
        assert response.status_code == 200

        # Verify enrollment
        enrollment = ClassEnrollment.query.filter_by(
            class_id=pending_class.class_id,
            student_id=sample_user.user_id
        ).first()
        assert enrollment is not None
        assert enrollment.enrollment_status == 'active'

    def test_class_rejection_flow(self, client, db_session, instructor_user, manager_user):
        """Test class proposal rejection flow"""
        # Instructor proposes class
        client.post('/auth/login', data={
            'username': 'instructor_test',
            'password': 'password123'
        })

        class_data = {
            'class_code': 'REJECT001',
            'class_name': 'To Reject',
            'description': 'This will be rejected',
            'level': 'beginner',
            'max_students': 10,
            'start_date': datetime.now().date().isoformat()
        }

        client.post('/instructor/propose-class', data=class_data, follow_redirects=True)
        pending_class = Class.query.filter_by(class_code='REJECT001').first()

        # Manager rejects
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'manager_test',
            'password': 'password123'
        })

        response = client.post(f'/manager/classes/{pending_class.class_id}/review',
                              data={'decision': 'reject', 'reason': 'Not suitable'},
                              follow_redirects=True)
        assert response.status_code == 200

        # Verify rejection
        db_session.refresh(pending_class)
        assert pending_class.approval_status == 'rejected'
        assert pending_class.is_active == False

    def test_class_enrollment_capacity_limit(self, client, db_session, approved_class, seed_roles):
        """Test class enrollment respects capacity limit"""
        # Set max_students to 1
        approved_class.max_students = 1
        db_session.commit()

        # Create two students
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        student1 = User(
            username='student1',
            email='student1@test.com',
            full_name='Student 1',
            role_id=student_role.role_id,
            is_active=True
        )
        student1.set_password('password123')
        db_session.add(student1)

        student2 = User(
            username='student2',
            email='student2@test.com',
            full_name='Student 2',
            role_id=student_role.role_id,
            is_active=True
        )
        student2.set_password('password123')
        db_session.add(student2)
        db_session.commit()

        # First student enrolls
        client.post('/auth/login', data={
            'username': 'student1',
            'password': 'password123'
        })
        response = client.post(f'/student/classes/{approved_class.class_id}/enroll',
                              follow_redirects=True)
        assert response.status_code == 200

        # Second student tries to enroll (should fail)
        client.get('/auth/logout')
        client.post('/auth/login', data={
            'username': 'student2',
            'password': 'password123'
        })
        response = client.post(f'/student/classes/{approved_class.class_id}/enroll',
                              follow_redirects=True)

        # Should show error about class being full
        response_text = response.data.decode('utf-8').lower()
        assert 'đầy' in response_text or 'full' in response_text or response.status_code != 200

