"""
Unit tests for UserService
"""
import pytest
from app.services.user_service import UserService
from app.models.user import User
from app.models.role import Role


class TestUserService:
    """Test UserService methods"""

    def test_create_user_success(self, db_session, seed_roles):
        """Test creating a user with valid data"""
        student_role = Role.query.filter_by(role_code='STUDENT').first()

        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123',
            'full_name': 'New User',
            'role_id': student_role.role_id
        }

        result = UserService.create_user(data)

        assert result['success'] == True
        assert result['user'].username == 'newuser'
        assert User.query.filter_by(username='newuser').first() is not None

    def test_create_user_duplicate_username(self, db_session, sample_user):
        """Test creating user with duplicate username fails"""
        data = {
            'username': 'test_student',  # Already exists
            'email': 'another@test.com',
            'password': 'password123',
            'full_name': 'Another User',
            'role_id': sample_user.role_id
        }

        result = UserService.create_user(data)

        assert result['success'] == False
        assert 'username' in result['message'].lower() or 'tên đăng nhập' in result['message'].lower()

    def test_create_user_duplicate_email(self, db_session, sample_user):
        """Test creating user with duplicate email fails"""
        data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Already exists
            'password': 'password123',
            'full_name': 'Another User',
            'role_id': sample_user.role_id
        }

        result = UserService.create_user(data)

        assert result['success'] == False
        assert 'email' in result['message'].lower() or 'đã được sử dụng' in result['message'].lower()

    def test_get_user_by_id(self, db_session, sample_user):
        """Test retrieving user by ID"""
        user = UserService.get_user_by_id(sample_user.user_id)

        assert user is not None
        assert user.username == 'test_student'

    def test_get_user_by_id_not_found(self, db_session):
        """Test retrieving non-existent user returns None"""
        user = UserService.get_user_by_id(99999)

        assert user is None

    def test_update_user_success(self, db_session, sample_user):
        """Test updating user information"""
        data = {
            'full_name': 'Updated Name',
            'email': 'updated@test.com',
            'role_id': sample_user.role_id,
            'is_active': True
        }

        result = UserService.update_user(sample_user.user_id, data)

        assert result['success'] == True
        updated = User.query.get(sample_user.user_id)
        assert updated.full_name == 'Updated Name'
        assert updated.email == 'updated@test.com'

    def test_update_user_not_found(self, db_session, seed_roles):
        """Test updating non-existent user fails"""
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        data = {
            'full_name': 'Updated Name',
            'email': 'updated@test.com',
            'role_id': student_role.role_id
        }

        result = UserService.update_user(99999, data)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower() or 'not found' in result['message'].lower()

    def test_update_user_duplicate_email(self, db_session, sample_user, seed_roles):
        """Test updating user with duplicate email fails"""
        # Create another user
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        other_user = User(
            username='otheruser',
            email='other@test.com',
            full_name='Other User',
            role_id=student_role.role_id,
            is_active=True
        )
        other_user.set_password('password123')
        db_session.add(other_user)
        db_session.commit()

        # Try to update sample_user with other_user's email
        data = {
            'full_name': 'Updated Name',
            'email': 'other@test.com',  # Already used
            'role_id': sample_user.role_id
        }

        result = UserService.update_user(sample_user.user_id, data)

        assert result['success'] == False
        assert 'email' in result['message'].lower() or 'đã được sử dụng' in result['message'].lower()

    def test_delete_user_success(self, db_session, sample_user):
        """Test deleting user"""
        user_id = sample_user.user_id

        result = UserService.delete_user(user_id)

        assert result['success'] == True
        assert User.query.get(user_id) is None

    def test_delete_user_not_found(self, db_session):
        """Test deleting non-existent user fails"""
        result = UserService.delete_user(99999)

        assert result['success'] == False
        assert 'không tìm thấy' in result['message'].lower() or 'not found' in result['message'].lower()

    def test_get_all_users(self, db_session, sample_user, instructor_user):
        """Test getting all users"""
        users = UserService.get_all_users()

        assert len(users) >= 2
        usernames = [u.username for u in users]
        assert 'test_student' in usernames
        assert 'instructor_test' in usernames

    def test_get_all_roles(self, db_session, seed_roles):
        """Test getting all active roles"""
        roles = UserService.get_all_roles()

        assert len(roles) == 4
        role_codes = [r.role_code for r in roles]
        assert 'STUDENT' in role_codes
        assert 'INSTRUCTOR' in role_codes
        assert 'MANAGER' in role_codes
        assert 'ADMIN' in role_codes

    def test_get_total_users_count(self, db_session, sample_user, instructor_user):
        """Test getting total users count"""
        count = UserService.get_total_users_count()

        assert count >= 2

    def test_get_users_count_by_role(self, db_session, sample_user, seed_roles):
        """Test getting users count by role"""
        student_count = UserService.get_users_count_by_role('STUDENT')
        assert student_count >= 1

        instructor_count = UserService.get_users_count_by_role('INSTRUCTOR')
        assert instructor_count >= 1

    def test_get_recent_users(self, db_session, sample_user):
        """Test getting recent users"""
        recent = UserService.get_recent_users(days=7, limit=10)

        assert len(recent) >= 1
        assert sample_user in recent

    def test_get_user_stats_by_role(self, db_session, sample_user, instructor_user, seed_roles):
        """Test getting user statistics by role"""
        stats = UserService.get_user_stats_by_role()

        assert 'STUDENT' in stats
        assert 'INSTRUCTOR' in stats
        assert stats['STUDENT']['count'] >= 1
        assert stats['INSTRUCTOR']['count'] >= 1

    def test_get_user_growth_percentage(self, db_session):
        """Test getting user growth percentage"""
        growth = UserService.get_user_growth_percentage(days=30)

        assert isinstance(growth, (int, float))
        assert growth >= 0

