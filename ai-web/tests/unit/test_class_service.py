"""
Unit tests for ClassService
"""
import pytest
from datetime import datetime, timedelta
from app.services.class_service import ClassService
from app.models.class_model import Class
from app.models.class_enrollment import ClassEnrollment
from app.models.user import User
from app.models.role import Role


class TestClassService:
    """Test ClassService methods"""

    def test_create_class_proposal_success(self, db_session, instructor_user):
        """Test creating a class proposal"""
        data = {
            'class_code': 'TEST001',
            'class_name': 'Test Class',
            'description': 'Test description',
            'level': 'beginner',
            'max_students': 20,
            'start_date': datetime.now().date(),
            'end_date': (datetime.now() + timedelta(days=30)).date()
        }

        result = ClassService.create_class_proposal(data, instructor_user.user_id)

        assert result['success'] == True
        assert result['class'].class_code == 'TEST001'
        assert result['class'].approval_status == 'pending'
        assert result['class'].is_active == False

    def test_create_class_proposal_duplicate_code(self, db_session, instructor_user, approved_class):
        """Test creating class proposal with duplicate code fails"""
        data = {
            'class_code': 'CLASS001',  # Already exists
            'class_name': 'Another Class',
            'level': 'beginner',
            'max_students': 15,
            'start_date': datetime.now().date()
        }

        result = ClassService.create_class_proposal(data, instructor_user.user_id)

        assert result['success'] == False
        assert 'mã lớp' in result['message'].lower() or 'code' in result['message'].lower()

    def test_get_pending_proposals(self, db_session, pending_class):
        """Test getting pending proposals"""
        proposals = ClassService.get_pending_proposals()

        assert len(proposals) >= 1
        assert pending_class in proposals

    def test_get_approved_classes_by_instructor(self, db_session, instructor_user, approved_class):
        """Test getting approved classes by instructor"""
        classes = ClassService.get_approved_classes_by_instructor(instructor_user.user_id)

        assert len(classes) >= 1
        assert approved_class in classes

    def test_get_my_proposals(self, db_session, instructor_user, pending_class, approved_class):
        """Test getting all proposals by instructor"""
        proposals = ClassService.get_my_proposals(instructor_user.user_id)

        assert len(proposals) >= 2
        class_ids = [c.class_id for c in proposals]
        assert pending_class.class_id in class_ids
        assert approved_class.class_id in class_ids

    def test_approve_class_success(self, db_session, pending_class, manager_user):
        """Test approving a class"""
        result = ClassService.approve_class(pending_class.class_id, manager_user.user_id)

        assert result['success'] == True
        assert result['class'].approval_status == 'approved'
        assert result['class'].is_active == True
        assert result['class'].approved_by == manager_user.user_id

    def test_approve_class_not_found(self, db_session, manager_user):
        """Test approving non-existent class fails"""
        result = ClassService.approve_class(99999, manager_user.user_id)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower()

    def test_approve_class_already_processed(self, db_session, approved_class, manager_user):
        """Test approving already processed class fails"""
        result = ClassService.approve_class(approved_class.class_id, manager_user.user_id)

        assert result['success'] == False
        assert 'đã được xử lý' in result['message'].lower() or 'already' in result['message'].lower()

    def test_reject_class_success(self, db_session, pending_class, manager_user):
        """Test rejecting a class"""
        reason = 'Not suitable for current curriculum'
        result = ClassService.reject_class(pending_class.class_id, manager_user.user_id, reason)

        assert result['success'] == True
        assert result['class'].approval_status == 'rejected'
        assert result['class'].is_active == False
        assert result['class'].rejection_reason == reason

    def test_reject_class_not_found(self, db_session, manager_user):
        """Test rejecting non-existent class fails"""
        result = ClassService.reject_class(99999, manager_user.user_id, 'Reason')

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower()

    def test_get_class_by_id(self, db_session, approved_class):
        """Test getting class by ID"""
        class_obj = ClassService.get_class_by_id(approved_class.class_id)

        assert class_obj is not None
        assert class_obj.class_code == 'CLASS001'

    def test_get_class_by_id_not_found(self, db_session):
        """Test getting non-existent class returns None"""
        class_obj = ClassService.get_class_by_id(99999)

        assert class_obj is None

    def test_update_class_success(self, db_session, approved_class):
        """Test updating class"""
        data = {
            'class_name': 'Updated Class Name',
            'description': 'Updated description',
            'level': 'intermediate',
            'max_students': 25,
            'end_date': (datetime.now() + timedelta(days=60)).date(),
            'is_active': True
        }

        result = ClassService.update_class(approved_class.class_id, data)

        assert result['success'] == True
        updated = Class.query.get(approved_class.class_id)
        assert updated.class_name == 'Updated Class Name'
        assert updated.max_students == 25

    def test_update_class_not_found(self, db_session):
        """Test updating non-existent class fails"""
        data = {
            'class_name': 'Updated',
            'level': 'beginner',
            'max_students': 20
        }

        result = ClassService.update_class(99999, data)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower()

    def test_delete_class_success(self, db_session, instructor_user):
        """Test deleting class"""
        # Create a class without enrollments
        data = {
            'class_code': 'DELETE001',
            'class_name': 'To Delete',
            'level': 'beginner',
            'max_students': 10,
            'start_date': datetime.now().date()
        }
        result = ClassService.create_class_proposal(data, instructor_user.user_id)
        class_id = result['class'].class_id

        # Approve it first
        from app.models.role import Role
        manager_role = Role.query.filter_by(role_code='MANAGER').first()
        manager = User.query.filter_by(role_id=manager_role.role_id).first()
        if manager:
            ClassService.approve_class(class_id, manager.user_id)

        delete_result = ClassService.delete_class(class_id)

        assert delete_result['success'] == True
        assert Class.query.get(class_id) is None

    def test_enroll_student_success(self, db_session, approved_class, sample_user):
        """Test enrolling student in class"""
        result = ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        assert result['success'] == True
        enrollment = ClassEnrollment.query.filter_by(
            class_id=approved_class.class_id,
            student_id=sample_user.user_id
        ).first()
        assert enrollment is not None
        assert enrollment.enrollment_status == 'active'

    def test_enroll_student_class_not_found(self, db_session, sample_user):
        """Test enrolling student in non-existent class fails"""
        result = ClassService.enroll_student(99999, sample_user.user_id)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower()

    def test_enroll_student_already_enrolled(self, db_session, approved_class, sample_user):
        """Test enrolling already enrolled student fails"""
        # Enroll once
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        # Try to enroll again
        result = ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        assert result['success'] == False
        assert 'đã đăng ký' in result['message'].lower() or 'already' in result['message'].lower()

    def test_enroll_student_class_full(self, db_session, instructor_user, sample_user, seed_roles):
        """Test enrolling student in full class fails"""
        # Create a class with max_students = 1
        data = {
            'class_code': 'FULL001',
            'class_name': 'Full Class',
            'level': 'beginner',
            'max_students': 1,
            'start_date': datetime.now().date()
        }
        result = ClassService.create_class_proposal(data, instructor_user.user_id)
        class_id = result['class'].class_id

        # Approve it
        manager_role = Role.query.filter_by(role_code='MANAGER').first()
        manager = User.query.filter_by(role_id=manager_role.role_id).first()
        if manager:
            ClassService.approve_class(class_id, manager.user_id)

        # Create another student and enroll them
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

        ClassService.enroll_student(class_id, other_student.user_id)

        # Try to enroll sample_user (should fail - class is full)
        enroll_result = ClassService.enroll_student(class_id, sample_user.user_id)

        assert enroll_result['success'] == False
        assert 'đầy' in enroll_result['message'].lower() or 'full' in enroll_result['message'].lower()

    def test_get_enrolled_students(self, db_session, approved_class, sample_user):
        """Test getting enrolled students"""
        # Enroll student
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        enrollments = ClassService.get_enrolled_students(approved_class.class_id)

        assert len(enrollments) >= 1
        student_ids = [e.student_id for e in enrollments]
        assert sample_user.user_id in student_ids

    def test_get_available_students(self, db_session, approved_class, sample_user):
        """Test getting available students"""
        available = ClassService.get_available_students(approved_class.class_id)

        assert sample_user in available

        # Enroll student
        ClassService.enroll_student(approved_class.class_id, sample_user.user_id)

        # Check again
        available_after = ClassService.get_available_students(approved_class.class_id)

        assert sample_user not in available_after

    def test_remove_student(self, db_session, approved_class, sample_user):
        """Test removing student from class"""
        # Enroll student
        enroll_result = ClassService.enroll_student(approved_class.class_id, sample_user.user_id)
        enrollment_id = enroll_result['enrollment'].enrollment_id

        # Remove student
        result = ClassService.remove_student(enrollment_id)

        assert result['success'] == True
        enrollment = ClassEnrollment.query.get(enrollment_id)
        assert enrollment is None

    def test_update_enrollment_status(self, db_session, approved_class, sample_user):
        """Test updating enrollment status"""
        # Enroll student
        enroll_result = ClassService.enroll_student(approved_class.class_id, sample_user.user_id)
        enrollment_id = enroll_result['enrollment'].enrollment_id

        # Update status
        result = ClassService.update_enrollment_status(enrollment_id, 'completed')

        assert result['success'] == True
        enrollment = ClassEnrollment.query.get(enrollment_id)
        assert enrollment.enrollment_status == 'completed'

    def test_get_statistics(self, db_session, approved_class, sample_user):
        """Test getting class statistics"""
        stats = ClassService.get_statistics()

        assert 'total_classes' in stats
        assert 'active_classes' in stats
        assert 'total_enrollments' in stats
        assert stats['total_classes'] >= 1

