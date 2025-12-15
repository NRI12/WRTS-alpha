from app import create_app, db
from app.models import (
    Role, User, Weapon, Class, ClassEnrollment, ClassSchedule,
    MartialRoutine, Assignment, TrainingVideo, ManualEvaluation,
    TrainingHistory, Notification, Exam, ExamResult, Feedback, AuthToken
)

app = create_app()

with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("Tables created successfully!")
    print("\nTables in database:")
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    for table in tables:
        print(f"  - {table}")

