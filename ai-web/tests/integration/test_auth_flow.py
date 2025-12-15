"""
Integration tests for authentication flow
"""
import pytest
from flask import session
from app.models.user import User
from app.models.role import Role


class TestAuthenticationFlow:
    """Test complete authentication workflows"""

    def test_registration_login_flow(self, client, db_session, seed_roles):
        """Test user can register and then login"""
        # Step 1: Register new user
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        register_data = {
            'username': 'integrationuser',
            'email': 'integration@test.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'Integration User',
            'role_id': student_role.role_id
        }

        response = client.post('/auth/register', data=register_data, follow_redirects=True)
        assert response.status_code == 200

        # Verify user was created
        user = User.query.filter_by(username='integrationuser').first()
        assert user is not None
        assert user.email == 'integration@test.com'

        # Step 2: Login with registered credentials
        login_data = {
            'username': 'integrationuser',
            'password': 'password123'
        }

        response = client.post('/auth/login', data=login_data, follow_redirects=True)
        assert response.status_code == 200

        # Step 3: Verify session is established
        with client.session_transaction() as sess:
            assert 'user_id' in sess
            assert sess['username'] == 'integrationuser'

    def test_login_wrong_password(self, client, sample_user):
        """Test login fails with incorrect password"""
        login_data = {
            'username': 'test_student',
            'password': 'wrongpassword'
        }

        response = client.post('/auth/login', data=login_data, follow_redirects=True)

        # Should show error message
        response_text = response.data.decode('utf-8').lower()
        assert 'invalid' in response_text or 'không đúng' in response_text or 'incorrect' in response_text

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username fails"""
        login_data = {
            'username': 'nonexistent',
            'password': 'password123'
        }

        response = client.post('/auth/login', data=login_data, follow_redirects=True)

        response_text = response.data.decode('utf-8').lower()
        assert 'invalid' in response_text or 'không đúng' in response_text or 'incorrect' in response_text

    def test_protected_route_requires_auth(self, client):
        """Test protected routes redirect to login"""
        response = client.get('/student/dashboard', follow_redirects=False)

        assert response.status_code == 302  # Redirect
        assert '/auth/login' in response.location

    def test_logout_clears_session(self, client, sample_user):
        """Test logout clears session"""
        # Login first
        login_data = {
            'username': 'test_student',
            'password': 'password123'
        }
        client.post('/auth/login', data=login_data, follow_redirects=True)

        # Verify session exists
        with client.session_transaction() as sess:
            assert 'user_id' in sess

        # Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200

        # Verify session cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess

    def test_duplicate_username_registration(self, client, db_session, sample_user, seed_roles):
        """Test registration with duplicate username fails"""
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        register_data = {
            'username': 'test_student',  # Already exists
            'email': 'newemail@test.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'New User',
            'role_id': student_role.role_id
        }

        response = client.post('/auth/register', data=register_data, follow_redirects=True)

        # Should show error
        response_text = response.data.decode('utf-8').lower()
        assert 'username' in response_text or 'tên đăng nhập' in response_text or 'đã tồn tại' in response_text

    def test_duplicate_email_registration(self, client, db_session, sample_user, seed_roles):
        """Test registration with duplicate email fails"""
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        register_data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Already exists
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'New User',
            'role_id': student_role.role_id
        }

        response = client.post('/auth/register', data=register_data, follow_redirects=True)

        # Should show error
        response_text = response.data.decode('utf-8').lower()
        assert 'email' in response_text or 'đã được sử dụng' in response_text

