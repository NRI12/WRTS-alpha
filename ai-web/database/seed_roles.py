import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from app.models.role import Role

def seed_roles():
    app = create_app()
    with app.app_context():
        # Xóa roles cũ (nếu có)
        Role.query.delete()
        
        # Tạo roles mới
        roles = [
            Role(
                role_name='Student',
                role_code='STUDENT',
                description='Học viên tập luyện võ thuật',
                permissions={'can_view_routines': True, 'can_upload_videos': True}
            ),
            Role(
                role_name='Instructor',
                role_code='INSTRUCTOR',
                description='Huấn luyện viên dạy võ thuật',
                permissions={'can_create_routines': True, 'can_evaluate': True, 'can_manage_classes': True}
            ),
            Role(
                role_name='Administrator',
                role_code='ADMIN',
                description='Quản trị viên hệ thống',
                permissions={'can_manage_users': True, 'can_manage_system': True}
            ),
            Role(
                role_name='Manager',
                role_code='MANAGER',
                description='Quản lý võ đường',
                permissions={'can_view_reports': True, 'can_view_analytics': True}
            )
        ]
        
        db.session.bulk_save_objects(roles)
        db.session.commit()
        
        print("SUCCESS: Đã seed 4 roles thành công!")

if __name__ == '__main__':
    seed_roles()
