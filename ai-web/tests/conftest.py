"""
Shared fixtures for pytest tests
"""
import pytest
import random
import numpy as np
from app import create_app, db
from app.models.user import User
from app.models.role import Role
from app.models.class_model import Class
from app.models.martial_routine import MartialRoutine
from app.models.weapon import Weapon
from app.models.class_enrollment import ClassEnrollment
from datetime import datetime, timedelta

# Set random seed for reproducible tests
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    import os
    # Set test database URI before creating app
    os.environ['DATABASE_URL'] = 'mysql+pymysql://root:password@localhost/AI_WRTS_TEST'
    os.environ['TESTING'] = 'True'
    
    # Import test config
    from app.test_config import TestConfig
    
    # Create app with TestConfig from the start
    app = create_app(config_class=TestConfig)
    
    with app.app_context():
        # Wait a bit if there's a concurrent DDL operation
        import time
        time.sleep(2)
        
        # Drop all tables first to ensure clean state
        try:
            db.drop_all()
        except Exception:
            pass  # Ignore if tables don't exist
        
        # Create all tables
        try:
            db.create_all()
        except Exception as e:
            # If there's still a concurrent DDL error, wait and retry
            if 'concurrent DDL' in str(e) or '1684' in str(e):
                time.sleep(5)
                db.create_all()
            else:
                raise
        
        yield app
        # Clean up
        try:
            db.drop_all()
        except Exception:
            pass


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        # Clear all tables
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        
        yield db.session
        
        db.session.rollback()


@pytest.fixture
def seed_roles(db_session):
    """Seed basic roles"""
    roles = [
        Role(role_code='STUDENT', role_name='Student', description='Student role'),
        Role(role_code='INSTRUCTOR', role_name='Instructor', description='Instructor role'),
        Role(role_code='MANAGER', role_name='Manager', description='Manager role'),
        Role(role_code='ADMIN', role_name='Admin', description='Admin role')
    ]
    for role in roles:
        db.session.add(role)
    db.session.commit()
    return roles


@pytest.fixture
def sample_user(db_session, seed_roles):
    """Create sample user"""
    student_role = Role.query.filter_by(role_code='STUDENT').first()
    user = User(
        username='test_student',
        email='test@example.com',
        full_name='Test Student',
        role_id=student_role.role_id,
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def instructor_user(db_session, seed_roles):
    """Create instructor user"""
    instructor_role = Role.query.filter_by(role_code='INSTRUCTOR').first()
    user = User(
        username='instructor_test',
        email='instructor@test.com',
        full_name='Test Instructor',
        role_id=instructor_role.role_id,
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def manager_user(db_session, seed_roles):
    """Create manager user"""
    manager_role = Role.query.filter_by(role_code='MANAGER').first()
    user = User(
        username='manager_test',
        email='manager@test.com',
        full_name='Test Manager',
        role_id=manager_role.role_id,
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(db_session, seed_roles):
    """Create admin user"""
    admin_role = Role.query.filter_by(role_code='ADMIN').first()
    user = User(
        username='admin_test',
        email='admin@test.com',
        full_name='Test Admin',
        role_id=admin_role.role_id,
        is_active=True
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_weapon(db_session):
    """Create sample weapon"""
    weapon = Weapon(
        weapon_code='SWORD',
        weapon_name_vi='Kiếm',
        weapon_name_en='Sword',
        is_active=True,
        display_order=1
    )
    db.session.add(weapon)
    db.session.commit()
    return weapon


@pytest.fixture
def sample_routine(db_session, instructor_user, sample_weapon):
    """Create sample routine"""
    routine = MartialRoutine(
        routine_code='ROUTINE001',
        routine_name='Test Routine',
        instructor_id=instructor_user.user_id,
        weapon_id=sample_weapon.weapon_id,
        level='beginner',
        difficulty_score=5.0,
        reference_video_url='/static/uploads/test_video.mp4',
        duration_seconds=60,
        total_moves=10,
        is_published=True,
        is_active=True,
        pass_threshold=70.0
    )
    db.session.add(routine)
    db.session.commit()
    return routine


@pytest.fixture
def approved_class(db_session, instructor_user, seed_roles, manager_user):
    """Create approved class"""
    class_obj = Class(
        class_code='CLASS001',
        class_name='Test Class',
        description='Test class description',
        instructor_id=instructor_user.user_id,
        level='beginner',
        max_students=20,
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date(),
        approval_status='approved',
        approved_by=manager_user.user_id,
        approved_at=datetime.now(),
        is_active=True
    )
    db.session.add(class_obj)
    db.session.commit()
    return class_obj


@pytest.fixture
def pending_class(db_session, instructor_user):
    """Create pending class proposal"""
    class_obj = Class(
        class_code='CLASS002',
        class_name='Pending Class',
        description='Pending class description',
        instructor_id=instructor_user.user_id,
        level='intermediate',
        max_students=15,
        start_date=datetime.now().date(),
        approval_status='pending',
        is_active=False
    )
    db.session.add(class_obj)
    db.session.commit()
    return class_obj

