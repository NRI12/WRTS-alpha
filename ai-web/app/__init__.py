from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from app.models import db
from app.config import Config
from datetime import datetime


migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    # Use provided config or default Config
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)
    
    # CSRF Configuration (uncomment để tắt CSRF tạm thời nếu cần debug)
    # app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Jinja global: now()
    @app.context_processor
    def inject_now():
        from app.utils.helpers import get_vietnam_time_naive
        return {
            'now': lambda: get_vietnam_time_naive()
        }
    
    # Jinja filters
    from app.utils.helpers import nl2br
    app.jinja_env.filters['nl2br'] = nl2br
    
    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, url_for, request
        max_size_mb = app.config.get('MAX_VIDEO_SIZE', 100 * 1024 * 1024) // (1024 * 1024)
        flash(f'File quá lớn! Vui lòng chọn file nhỏ hơn {max_size_mb}MB.', 'error')
        # Redirect về trang trước đó hoặc trang chính
        if request.referrer:
            return redirect(request.referrer)
        return redirect(url_for('instructor.assignments'))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.student_videos import student_videos_bp
    from app.routes.instructor import instructor_bp
    from app.routes.admin import admin_bp
    from app.routes.manager import manager_bp
    from app.routes.shared import shared_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(student_videos_bp)
    app.register_blueprint(instructor_bp, url_prefix='/instructor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(shared_bp)
    
    return app