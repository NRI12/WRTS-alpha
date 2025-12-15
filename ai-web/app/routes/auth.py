from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import AuthService
from app.utils.decorators import login_required, role_required
from app.forms.auth_forms import (
    LoginForm, RegisterForm, ForgotPasswordForm, 
    ResetPasswordForm, ChangePasswordForm, EditProfileForm
)
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ============ PUBLIC ROUTES ============

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('shared.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.login(form.username.data, form.password.data)
        if user:
            session.permanent = True
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role_code'] = user.role.role_code
            session['full_name'] = user.full_name
            
            # Redirect theo role
            if user.role.role_code == 'STUDENT':
                return redirect(url_for('student.dashboard'))
            elif user.role.role_code == 'INSTRUCTOR':
                return redirect(url_for('instructor.dashboard'))
            elif user.role.role_code == 'ADMIN':
                return redirect(url_for('admin.dashboard'))
            elif user.role.role_code == 'MANAGER':
                return redirect(url_for('manager.dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('shared.home'))
    form = RegisterForm()
    
    # DEBUG: Hiện form errors nếu validation fail
    if form.is_submitted():
        if not form.validate():
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    if form.validate_on_submit():
        data = {
            'username': form.username.data,
            'password': form.password.data,
            'email': form.email.data,
            'full_name': form.full_name.data,
            'phone': form.phone.data or None,
            'date_of_birth': form.date_of_birth.data,
            'gender': form.gender.data if form.gender.data else None,
            'address': form.address.data or None
        }
        
        result = AuthService.register_student(data)
        if result['success']:
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['message'], 'error')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        result = AuthService.send_reset_password_email(form.email.data)
        if result['success']:
            flash('Email khôi phục mật khẩu đã được gửi!', 'success')
        else:
            flash(result['message'], 'error')
    
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        result = AuthService.reset_password(token, form.new_password.data)
        if result['success']:
            flash('Đặt lại mật khẩu thành công!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['message'], 'error')
    
    return render_template('auth/reset_password.html', form=form, token=token)


@auth_bp.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Đã đăng xuất', 'success')
    return redirect(url_for('auth.login'))


# ============ AUTHENTICATED ROUTES ============

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        result = AuthService.change_password(
            session['user_id'], 
            form.current_password.data, 
            form.new_password.data
        )
        if result['success']:
            flash('Đổi mật khẩu thành công!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(result['message'], 'error')
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    user = AuthService.get_user_by_id(session['user_id'])
    if not user:
        flash('Tài khoản không tồn tại hoặc đã bị vô hiệu hóa.', 'error')
        return redirect(url_for('auth.login'))
    return render_template('auth/profile.html', user=user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = AuthService.get_user_by_id(session['user_id'])
    form = EditProfileForm(obj=user)
    
    if form.validate_on_submit():
        data = {
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'date_of_birth': form.date_of_birth.data,
            'gender': form.gender.data if form.gender.data else None,
            'address': form.address.data
        }
        
        result = AuthService.update_profile(session['user_id'], data)
        if result['success']:
            flash('Cập nhật thông tin thành công!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(result['message'], 'error')
    
    return render_template('auth/edit_profile.html', form=form, user=user)