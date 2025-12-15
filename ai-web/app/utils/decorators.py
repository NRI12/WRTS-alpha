from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role_code' not in session:
                flash('Vui lòng đăng nhập', 'error')
                return redirect(url_for('auth.login'))
            
            if session['role_code'] not in roles:
                flash('Bạn không có quyền truy cập', 'error')
                return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
