import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from app.models.role import Role
from app.models.user import User
from app.models.weapon import Weapon

def run_seed():
    app = create_app()
    with app.app_context():
        role_specs = [
            dict(role_name='Student', role_code='STUDENT', description='Học viên tập luyện võ thuật', permissions={'can_view_routines': True, 'can_upload_videos': True}),
            dict(role_name='Instructor', role_code='INSTRUCTOR', description='Huấn luyện viên dạy võ thuật', permissions={'can_create_routines': True, 'can_evaluate': True, 'can_manage_classes': True}),
            dict(role_name='Administrator', role_code='ADMIN', description='Quản trị viên hệ thống', permissions={'can_manage_users': True, 'can_manage_system': True}),
            dict(role_name='Manager', role_code='MANAGER', description='Quản lý võ đường', permissions={'can_view_reports': True, 'can_view_analytics': True}),
        ]
        for spec in role_specs:
            if not Role.query.filter_by(role_code=spec['role_code']).first():
                db.session.add(Role(**spec))

        admin_role = Role.query.filter_by(role_code='ADMIN').first()
        if admin_role and not User.query.filter_by(username='admin').first():
            u = User(username='admin', email='admin@example.com', full_name='Quản trị viên', role_id=admin_role.role_id, is_active=True, is_email_verified=True)
            u.set_password('admin123')
            db.session.add(u)

        weapons_seed = [
            {'weapon_code': 'SWORD', 'weapon_name_vi': 'Kiếm', 'weapon_name_en': 'Sword', 'display_order': 1},
            {'weapon_code': 'SPEAR', 'weapon_name_vi': 'Thương', 'weapon_name_en': 'Spear', 'display_order': 2},
            {'weapon_code': 'STAFF', 'weapon_name_vi': 'Côn', 'weapon_name_en': 'Staff', 'display_order': 3},
            {'weapon_code': 'HALBERD', 'weapon_name_vi': 'Kích', 'weapon_name_en': 'Halberd', 'display_order': 4},
        ]
        for w in weapons_seed:
            exists = Weapon.query.filter((Weapon.weapon_code == w['weapon_code']) | (Weapon.weapon_name_vi == w['weapon_name_vi']) | (Weapon.weapon_name_en == w['weapon_name_en'])).first()
            if not exists:
                db.session.add(Weapon(weapon_code=w['weapon_code'], weapon_name_vi=w['weapon_name_vi'], weapon_name_en=w['weapon_name_en'], display_order=w['display_order'], is_active=True))

        instructor_role = Role.query.filter_by(role_code='INSTRUCTOR').first()
        if instructor_role and not User.query.filter_by(username='instructor1').first():
            u = User(username='instructor1', email='instructor@test.com', full_name='Huấn Luyện Viên Test', phone='0912345678', role_id=instructor_role.role_id, is_active=True, is_email_verified=True)
            u.set_password('instructor123')
            db.session.add(u)

        manager_role = Role.query.filter_by(role_code='MANAGER').first()
        if manager_role and not User.query.filter_by(username='manager1').first():
            u = User(username='manager1', email='manager@test.com', full_name='Quản Lý Võ Đường Test', phone='0923456789', role_id=manager_role.role_id, is_active=True, is_email_verified=True)
            u.set_password('manager123')
            db.session.add(u)

        student_role = Role.query.filter_by(role_code='STUDENT').first()
        if student_role:
            for i in range(1, 6):
                username = f'student{i}'
                if not User.query.filter_by(username=username).first():
                    u = User(username=username, email=f'student{i}@test.com', full_name=f'Học Viên Test {i}', phone=f'093456789{i}', role_id=student_role.role_id, is_active=True, is_email_verified=True)
                    u.set_password('student123')
                    db.session.add(u)

        db.session.commit()

if __name__ == '__main__':
    run_seed()


