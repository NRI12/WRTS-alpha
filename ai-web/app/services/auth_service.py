from app.models import db
from app.models.user import User
from app.models.role import Role
from app.models.auth_token import AuthToken
from app.utils.helpers import get_vietnam_time
from datetime import datetime, timedelta
import secrets

class AuthService:
    
    @staticmethod
    def login(username, password):
        user = User.query.filter_by(username=username, is_active=True).first()
        if user and user.check_password(password):
            user.last_login_at = get_vietnam_time()
            db.session.commit()
            return user
        return None
    
    @staticmethod
    def register_student(data):
        # Kiểm tra username đã tồn tại
        if User.query.filter_by(username=data['username']).first():
            return {'success': False, 'message': 'Tên đăng nhập đã tồn tại'}
        
        # Kiểm tra email đã tồn tại
        if User.query.filter_by(email=data['email']).first():
            return {'success': False, 'message': 'Email đã được sử dụng'}
        
        # Lấy role STUDENT
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        if not student_role:
            return {'success': False, 'message': 'Không tìm thấy role học viên'}
        
        # Tạo user mới
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            address=data.get('address'),
            role_id=student_role.role_id
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return {'success': True, 'user': user}
    
    @staticmethod
    def send_reset_password_email(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            return {'success': False, 'message': 'Email không tồn tại'}
        
        # Tạo reset token
        token = secrets.token_urlsafe(32)
        auth_token = AuthToken(
            user_id=user.user_id,
            token_hash=token,
            token_type='reset_password',
            expires_at=get_vietnam_time() + timedelta(hours=24)
        )
        db.session.add(auth_token)
        db.session.commit()
        
        # TODO: Gửi email (implement sau)
        # EmailService.send_reset_password_email(user.email, token)
        
        return {'success': True, 'token': token}
    
    @staticmethod
    def reset_password(token, new_password):
        auth_token = AuthToken.query.filter_by(
            token_hash=token,
            token_type='reset_password',
            is_revoked=False
        ).first()
        
        if not auth_token:
            return {'success': False, 'message': 'Token không hợp lệ'}
        
        if auth_token.expires_at < get_vietnam_time():
            return {'success': False, 'message': 'Token đã hết hạn'}
        
        # Đặt lại mật khẩu
        user = auth_token.user
        user.set_password(new_password)
        
        # Revoke token
        auth_token.is_revoked = True
        auth_token.used_at = get_vietnam_time()
        
        db.session.commit()
        return {'success': True}
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'Không tìm thấy người dùng'}
        
        if not user.check_password(current_password):
            return {'success': False, 'message': 'Mật khẩu hiện tại không đúng'}
        
        user.set_password(new_password)
        db.session.commit()
        return {'success': True}
    
    @staticmethod
    def update_profile(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'Không tìm thấy người dùng'}
        
        user.full_name = data.get('full_name', user.full_name)
        user.phone = data.get('phone', user.phone)
        user.date_of_birth = data.get('date_of_birth', user.date_of_birth)
        user.gender = data.get('gender', user.gender)
        user.address = data.get('address', user.address)
        
        db.session.commit()
        return {'success': True, 'user': user}
    
    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
