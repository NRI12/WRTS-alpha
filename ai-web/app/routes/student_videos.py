from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.services.video_service import VideoService
from functools import wraps

student_videos_bp = Blueprint('student_videos', __name__, url_prefix='/student/videos')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('role_code') != 'STUDENT':
            flash('Chỉ học viên mới có quyền truy cập', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_videos_bp.route('/result/<int:video_id>')
@student_required
def view_result(video_id):
    """Xem kết quả phân tích - redirect đến video detail với tab result"""
    return redirect(url_for('student_videos.video_detail', video_id=video_id, tab='result'))

@student_videos_bp.route('/compare/<int:video_id>')
@student_required
def compare(video_id):
    """So sánh video với video mẫu - redirect đến video detail với tab compare"""
    return redirect(url_for('student_videos.video_detail', video_id=video_id, tab='compare'))

@student_videos_bp.route('/detail/<int:video_id>')
@student_required
def video_detail(video_id):
    """Trang chi tiết video thống nhất với tabs cho kết quả và so sánh"""
    # Lấy thông tin video với phân tích
    result = VideoService.get_video_with_analysis(video_id)
    
    if not result:
        flash('Video không tồn tại', 'danger')
        return redirect(url_for('student.my_assignments'))
    
    video = result.get('video')
    
    # Kiểm tra quyền truy cập
    if video.student_id != session.get('user_id'):
        flash('Bạn không có quyền xem video này', 'danger')
        return redirect(url_for('student.my_assignments'))
    
    # Lấy video mẫu chuẩn: luôn dùng video demo giảng viên gắn với assignment
    reference_video = video.assignment.instructor_video_url if video.assignment and video.assignment.instructor_video_url else None
    
    # Chuẩn bị dữ liệu cho template
    template_data = {
        'video': video,
        'student_video': video,  # Để tương thích với tab compare
        'reference_video': reference_video,
        **{k: v for k, v in result.items() if k != 'video'}  # Thêm các dữ liệu khác từ result
    }
    
    return render_template('student/video_detail.html', **template_data)