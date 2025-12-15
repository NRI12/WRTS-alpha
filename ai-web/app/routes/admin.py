from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.user_service import UserService
from app.utils.decorators import login_required, role_required
from app.forms.admin_forms import CreateUserForm, EditUserForm
from app.forms.feedback_forms import FeedbackResponseForm
from app.services.feedback_service import FeedbackService
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def get_recent_activities():
    """Get recent system activities for dashboard"""
    activities = []
    
    try:
        # Get recent user registrations (last 7 days)
        recent_users = UserService.get_recent_users(days=7)
        for user in recent_users:
            role_name = 'người dùng'
            try:
                if hasattr(user, 'role') and user.role:
                    role_name = user.role.role_name.lower()
            except:
                pass
            
            activities.append({
                'type': 'user_registration',
                'title': 'Người dùng mới đăng ký',
                'description': f'{user.full_name or user.username} đã đăng ký tài khoản {role_name}',
                'timestamp': user.created_at,
                'icon': 'fas fa-user-plus',
                'color': 'bg-primary'
            })
        
        # Get recent feedback submissions (last 7 days)
        recent_feedback = FeedbackService.get_recent_feedback(days=7, limit=5)
        for feedback in recent_feedback:
            user_name = 'Người dùng'
            try:
                if hasattr(feedback, 'user') and feedback.user:
                    user_name = feedback.user.full_name or feedback.user.username
            except:
                pass
            
            activities.append({
                'type': 'feedback_submission',
                'title': 'Phản hồi mới',
                'description': f'{user_name} gửi phản hồi: {feedback.subject or "Không có tiêu đề"}',
                'timestamp': feedback.created_at,
                'icon': 'fas fa-comment',
                'color': 'bg-info'
            })
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min, reverse=True)
        
        # Return only the 10 most recent activities
        return activities[:10]
        
    except Exception as e:
        print(f"Error getting recent activities: {e}")
        return []

@admin_bp.route('/dashboard')
@login_required
@role_required('ADMIN')
def dashboard():
    # Get real statistics from database
    try:
        stats = {
            'total_users': UserService.get_total_users_count(),
            'total_students': UserService.get_users_count_by_role('STUDENT'),
            'total_instructors': UserService.get_users_count_by_role('INSTRUCTOR'),
            'total_managers': UserService.get_users_count_by_role('MANAGER'),
            'total_admins': UserService.get_users_count_by_role('ADMIN'),
            'total_feedback': FeedbackService.get_total_feedback_count(),
            'pending_feedback': FeedbackService.get_feedback_count_by_status('pending'),
            'resolved_feedback': FeedbackService.get_feedback_count_by_status('resolved'),
            'user_growth_percentage': UserService.get_user_growth_percentage(30),
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        stats = {
            'total_users': 0,
            'total_students': 0,
            'total_instructors': 0,
            'total_managers': 0,
            'total_admins': 0,
            'total_feedback': 0,
            'pending_feedback': 0,
            'resolved_feedback': 0,
            'user_growth_percentage': 0,
        }
    
    # Get recent activity (last 10 activities)
    recent_activities = get_recent_activities()
    
    # Get recent feedback (last 5 feedbacks)
    try:
        recent_feedback = FeedbackService.get_recent_feedback(limit=5)
    except Exception as e:
        print(f"Error getting recent feedback: {e}")
        recent_feedback = []
    
    return render_template('admin/dashboard.html', 
                         **stats,
                         recent_activities=recent_activities,
                         recent_feedback=recent_feedback)

@admin_bp.route('/users')
@login_required
@role_required('ADMIN')
def users():
    users = UserService.get_all_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def create_user():
    form = CreateUserForm()
    
    # Load roles vào SelectField
    roles = UserService.get_all_roles()
    form.role_id.choices = [(0, '-- Chọn vai trò --')] + [(r.role_id, r.role_name) for r in roles]
    
    if form.validate_on_submit():
        data = {
            'username': form.username.data,
            'password': form.password.data,
            'email': form.email.data,
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'date_of_birth': form.date_of_birth.data,
            'gender': form.gender.data if form.gender.data else None,
            'address': form.address.data,
            'role_id': form.role_id.data
        }
        
        result = UserService.create_user(data)
        if result['success']:
            flash('Tạo tài khoản thành công!', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(result['message'], 'error')
    
    return render_template('admin/user_create.html', form=form)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def edit_user(user_id):
    user = UserService.get_user_by_id(user_id)
    form = EditUserForm(obj=user)
    
    # Load roles vào SelectField
    roles = UserService.get_all_roles()
    form.role_id.choices = [(r.role_id, r.role_name) for r in roles]
    
    if form.validate_on_submit():
        data = {
            'email': form.email.data,
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'date_of_birth': form.date_of_birth.data,
            'gender': form.gender.data if form.gender.data else None,
            'address': form.address.data,
            'role_id': form.role_id.data,
            'is_active': form.is_active.data
        }
        
        result = UserService.update_user(user_id, data)
        if result['success']:
            flash('Cập nhật thành công!', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(result['message'], 'error')
    
    return render_template('admin/user_edit.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('ADMIN')
def delete_user(user_id):
    result = UserService.delete_user(user_id)
    if result['success']:
        flash('Xóa tài khoản thành công!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin.users'))


# ============ FEEDBACK MANAGEMENT ============

@admin_bp.route('/feedback')
@login_required
@role_required('ADMIN')
def feedback_list():
    """Danh sách feedback"""
    status = request.args.get('status')
    feedback_type = request.args.get('type')
    
    filters = {}
    if status:
        filters['status'] = status
    if feedback_type:
        filters['type'] = feedback_type
    
    feedbacks = FeedbackService.get_all_feedback(filters)
    return render_template('admin/feedback_list.html', feedbacks=feedbacks)

@admin_bp.route('/feedback/<int:feedback_id>', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def feedback_detail(feedback_id):
    """Chi tiết & xử lý feedback"""
    feedback = FeedbackService.get_feedback_by_id(feedback_id)
    if not feedback:
        flash('Không tìm thấy phản hồi', 'error')
        return redirect(url_for('admin.feedback_list'))
    
    form = FeedbackResponseForm(obj=feedback)
    
    if form.validate_on_submit():
        data = {
            'priority': form.priority.data,
            'feedback_status': form.feedback_status.data,
            'resolution_notes': form.resolution_notes.data
        }
        
        result = FeedbackService.update_feedback(feedback_id, data)
        
        if result['success']:
            flash('Cập nhật phản hồi thành công!', 'success')
            return redirect(url_for('admin.feedback_list'))
        else:
            flash(result['message'], 'error')
    
    return render_template('admin/feedback_detail.html', 
                         feedback=feedback, 
                         form=form)
