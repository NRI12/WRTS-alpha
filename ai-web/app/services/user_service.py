from app.models import db
from app.models.user import User
from app.models.role import Role
from datetime import datetime, timedelta
from sqlalchemy import func

class UserService:
    
    @staticmethod
    def get_all_users():
        return User.query.all()
    
    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)
    
    @staticmethod
    def get_all_roles():
        return Role.query.filter_by(is_active=True).all()
    
    @staticmethod
    def create_user(data):
        # Kiểm tra username
        if User.query.filter_by(username=data['username']).first():
            return {'success': False, 'message': 'Tên đăng nhập đã tồn tại'}
        
        # Kiểm tra email
        if User.query.filter_by(email=data['email']).first():
            return {'success': False, 'message': 'Email đã được sử dụng'}
        
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender'),
            address=data.get('address'),
            role_id=data['role_id']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        return {'success': True, 'user': user}
    
    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'Không tìm thấy người dùng'}
        
        # Kiểm tra email trùng
        existing_email = User.query.filter(
            User.email == data['email'],
            User.user_id != user_id
        ).first()
        if existing_email:
            return {'success': False, 'message': 'Email đã được sử dụng'}
        
        user.email = data['email']
        user.full_name = data['full_name']
        user.phone = data.get('phone')
        user.date_of_birth = data.get('date_of_birth')
        user.gender = data.get('gender')
        user.address = data.get('address')
        user.role_id = data['role_id']
        user.is_active = data.get('is_active', True)
        
        db.session.commit()
        return {'success': True, 'user': user}
    
    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': 'Không tìm thấy người dùng'}
        
        db.session.delete(user)
        db.session.commit()
        return {'success': True}
    
    @staticmethod
    def get_total_users_count():
        """Get total number of users"""
        return User.query.filter(User.is_active == True).count()
    
    @staticmethod
    def get_users_count_by_role(role_code):
        """Get count of users by role code"""
        return db.session.query(User).join(Role).filter(
            Role.role_code == role_code,
            User.is_active == True
        ).count()
    
    @staticmethod
    def get_recent_users(days=7, limit=10):
        """Get recent users registered in the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return User.query.filter(
            User.created_at >= cutoff_date
        ).order_by(User.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_user_stats_by_role():
        """Get user statistics grouped by role"""
        stats = db.session.query(
            Role.role_code,
            Role.role_name,
            func.count(User.user_id).label('count')
        ).join(User).filter(
            User.is_active == True
        ).group_by(Role.role_code, Role.role_name).all()
        
        return {stat.role_code: {'name': stat.role_name, 'count': stat.count} for stat in stats}
    
    @staticmethod
    def get_user_growth_percentage(days=30):
        """Get user growth percentage compared to previous period"""
        try:
            current_period_start = datetime.now() - timedelta(days=days)
            previous_period_start = current_period_start - timedelta(days=days)
            
            current_count = User.query.filter(
                User.created_at >= current_period_start,
                User.is_active == True
            ).count()
            previous_count = User.query.filter(
                User.created_at >= previous_period_start,
                User.created_at < current_period_start,
                User.is_active == True
            ).count()
            
            if previous_count == 0:
                return 100 if current_count > 0 else 0
            
            return round(((current_count - previous_count) / previous_count) * 100, 1)
        except Exception as e:
            print(f"Error calculating user growth: {e}")
            return 0
