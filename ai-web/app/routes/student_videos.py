from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms.video_forms import VideoFilterForm
from app.services.video_service import VideoService
from app.services.weapon_detection_service import WeaponDetectionService
from app.models.martial_routine import MartialRoutine
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

@student_videos_bp.route('/history')
@student_required
def history():
    """Lịch sử nộp bài"""
    filter_form = VideoFilterForm()
    
    # Load danh sách bài võ cho filter (dùng 0 cho "Tất cả")
    routines = MartialRoutine.query.filter_by(is_published=True).all()
    filter_form.routine_id.choices = [(0, 'Tất cả')] + [(r.routine_id, r.routine_name) for r in routines]
    
    # Set choices cho status
    filter_form.status.choices = [
        ('', 'Tất cả'),
        ('pending', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại')
    ]
    
    # Lấy filter params
    routine_id = request.args.get('routine_id', type=int)
    status = request.args.get('status')
    
    # Nếu routine_id = 0 thì bỏ filter
    if routine_id == 0:
        routine_id = None
    
    # Nếu status = '' thì bỏ filter
    if status == '':
        status = None
    
    # Gán lại giá trị vào form để giữ trạng thái đã chọn
    filter_form.routine_id.data = routine_id if routine_id is not None else 0
    filter_form.status.data = status if status is not None else ''

    # Lấy danh sách video
    videos = VideoService.get_student_videos(
        student_id=session.get('user_id'),
        routine_id=routine_id,
        status=status
    )
    
    return render_template('student/video_history.html', 
                         videos=videos, 
                         filter_form=filter_form)

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
        return redirect(url_for('student_videos.history'))
    
    video = result.get('video')
    
    # Kiểm tra quyền truy cập
    if video.student_id != session.get('user_id'):
        flash('Bạn không có quyền xem video này', 'danger')
        return redirect(url_for('student_videos.history'))
    
    # Lấy video mẫu chuẩn
    reference_video = video.routine.reference_video_url if video.routine else None
    
    # Chuẩn bị dữ liệu cho template
    template_data = {
        'video': video,
        'student_video': video,  # Để tương thích với tab compare
        'reference_video': reference_video,
        **{k: v for k, v in result.items() if k != 'video'}  # Thêm các dữ liệu khác từ result
    }
    
    return render_template('student/video_detail.html', **template_data)