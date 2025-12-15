# ============================================
# database/seed_test_users.py
# ============================================
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.role import Role

def seed_test_users():
    app = create_app()
    with app.app_context():
        # Tạo INSTRUCTOR
        instructor_role = Role.query.filter_by(role_code='INSTRUCTOR').first()
        if not instructor_role:
            print("❌ Chưa có role INSTRUCTOR. Chạy seed_roles.py trước!")
            return
            
        if not User.query.filter_by(username='instructor1').first():
            instructor = User(
                username='instructor1',
                email='instructor@test.com',
                full_name='Huấn Luyện Viên Test',
                phone='0912345678',
                role_id=instructor_role.role_id,
                is_active=True,
                is_email_verified=True
            )
            instructor.set_password('instructor123')
            db.session.add(instructor)
            print("✅ Tạo instructor: instructor1 / instructor123")
        else:
            print("ℹ️  instructor1 đã tồn tại")
        
        # Tạo MANAGER
        manager_role = Role.query.filter_by(role_code='MANAGER').first()
        if not manager_role:
            print("❌ Chưa có role MANAGER. Chạy seed_roles.py trước!")
            return
            
        if not User.query.filter_by(username='manager1').first():
            manager = User(
                username='manager1',
                email='manager@test.com',
                full_name='Quản Lý Võ Đường Test',
                phone='0923456789',
                role_id=manager_role.role_id,
                is_active=True,
                is_email_verified=True
            )
            manager.set_password('manager123')
            db.session.add(manager)
            print("✅ Tạo manager: manager1 / manager123")
        else:
            print("ℹ️  manager1 đã tồn tại")
        
        # Tạo vài STUDENT để test enroll vào lớp
        student_role = Role.query.filter_by(role_code='STUDENT').first()
        if not student_role:
            print("❌ Chưa có role STUDENT. Chạy seed_roles.py trước!")
            return
            
        for i in range(1, 6):  # Tạo 5 học viên
            username = f'student{i}'
            if not User.query.filter_by(username=username).first():
                student = User(
                    username=username,
                    email=f'student{i}@test.com',
                    full_name=f'Học Viên Test {i}',
                    phone=f'093456789{i}',
                    role_id=student_role.role_id,
                    is_active=True,
                    is_email_verified=True
                )
                student.set_password('student123')
                db.session.add(student)
                print(f"✅ Tạo student: {username} / student123")
            else:
                print(f"ℹ️  {username} đã tồn tại")
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ SEED TEST USERS HOÀN TẤT!")
        print("="*50)
        print("\nTÀI KHOẢN TEST:")
        print("-" * 50)
        print("INSTRUCTOR:")
        print("  Username: instructor1")
        print("  Password: instructor123")
        print()
        print("MANAGER:")
        print("  Username: manager1")
        print("  Password: manager123")
        print()
        print("STUDENT (5 tài khoản):")
        print("  Username: student1 -> student5")
        print("  Password: student123")
        print("="*50)

if __name__ == '__main__':
    seed_test_users()