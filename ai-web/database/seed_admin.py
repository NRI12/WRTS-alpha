import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.role import Role

def seed_admin():
    app = create_app()
    with app.app_context():
        # Lấy role ADMIN
        admin_role = Role.query.filter_by(role_code='ADMIN').first()
        if not admin_role:
            print("ERROR: Chưa có role ADMIN. Chạy seed_roles.py trước!")
            return
        
        # Kiểm tra admin đã tồn tại chưa
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print("INFO: Admin user đã tồn tại")
            return
        
        # Tạo admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Quản trị viên',
            role_id=admin_role.role_id,
            is_active=True,
            is_email_verified=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("SUCCESS: Đã tạo admin user:")
        print("   Username: admin")
        print("   Password: admin123")

if __name__ == '__main__':
    seed_admin()
