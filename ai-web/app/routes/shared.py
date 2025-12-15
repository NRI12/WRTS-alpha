from flask import Blueprint, render_template, redirect, url_for, flash, session, request, Response, stream_with_context
from app.utils.decorators import login_required
from app.utils.storage_service import StorageService
from app.forms.feedback_forms import FeedbackSubmitForm
from app.services.feedback_service import FeedbackService
from app.services.analytics_service import AnalyticsService
import requests

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/')
def home():
    """Trang chủ (landing page) với dữ liệu thật"""
    # Thống kê tổng quan hệ thống
    try:
        system_overview = AnalyticsService.get_system_overview()
    except Exception:
        system_overview = None

    # Một vài feedback gần đây (ẩn nội dung chi tiết, chỉ hiển thị tiêu đề)
    try:
        recent_feedback = FeedbackService.get_recent_feedback(limit=3)
    except Exception:
        recent_feedback = []

    # Thông tin đăng nhập hiện tại (nếu có) để hiển thị CTA phù hợp
    role_code = session.get('role_code')
    is_logged_in = bool(session.get('user_id'))

    role_dashboard = None
    if role_code == 'STUDENT':
        role_dashboard = url_for('student.dashboard')
    elif role_code == 'INSTRUCTOR':
        role_dashboard = url_for('instructor.dashboard')
    elif role_code == 'ADMIN':
        role_dashboard = url_for('admin.dashboard')
    elif role_code == 'MANAGER':
        role_dashboard = url_for('manager.dashboard')

    return render_template(
        'home.html',
        system_overview=system_overview,
        recent_feedback=recent_feedback,
        is_logged_in=is_logged_in,
        role_code=role_code,
        role_dashboard=role_dashboard,
    )

@shared_bp.route('/feedback/submit', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    """Submit feedback (all roles)"""
    form = FeedbackSubmitForm()
    
    if form.validate_on_submit():
        data = {
            'feedback_type': form.feedback_type.data,
            'subject': form.subject.data,
            'content': form.content.data
        }
        
        result = FeedbackService.create_feedback(session['user_id'], data)
        
        if result['success']:
            flash('Gửi phản hồi thành công! Cảm ơn bạn đã đóng góp.', 'success')
            return redirect(url_for('shared.my_feedback'))
        else:
            flash('Có lỗi xảy ra', 'error')
    
    return render_template('shared/feedback_submit.html', form=form)

@shared_bp.route('/feedback/my')
@login_required
def my_feedback():
    """Xem feedback của mình"""
    feedbacks = FeedbackService.get_user_feedback(session['user_id'])
    return render_template('shared/my_feedback.html', feedbacks=feedbacks)

@shared_bp.route('/storage/<path:file_path>')
def serve_storage_file(file_path):
    """Proxy route để serve file từ Railway storage"""
    try:
        s3_client, bucket_name = StorageService._get_s3_client()
        file_url = f"https://storage.railway.app/{bucket_name}/{file_path}"
        
        presigned_url = StorageService.get_presigned_url(file_url, expiration=3600)
        
        response = requests.get(presigned_url, stream=True, timeout=30)
        response.raise_for_status()
        
        headers = {
            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream'),
            'Content-Length': response.headers.get('Content-Length'),
            'Cache-Control': 'public, max-age=3600'
        }
        
        return Response(
            stream_with_context(response.iter_content(chunk_size=8192)),
            headers=headers,
            status=response.status_code
        )
    except Exception as e:
        return f"Error serving file: {str(e)}", 500