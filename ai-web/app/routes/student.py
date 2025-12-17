from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from app.utils.decorators import login_required, role_required
from app.utils.helpers import get_vietnam_time, get_vietnam_time_naive
from app.models.class_enrollment import ClassEnrollment
from app.models.class_model import Class
from app.models.class_schedule import ClassSchedule
from app.models.user import User
from app.models import db
from sqlalchemy import and_
from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService
from app.services.video_service import VideoService
from app.services.weapon_detection_service import WeaponDetectionService
from werkzeug.utils import secure_filename
import tempfile
import os


student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard')
@login_required
@role_required('STUDENT')
def dashboard():
    # Thống kê nhanh
    student_id = session['user_id']

    # Đếm lớp đang học
    active_classes = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).count()

    # Đếm lớp đã hoàn thành
    completed_classes = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='completed'
    ).count()

    # Lấy lịch học hôm nay (lấy 5 lịch gần nhất)
    today = get_vietnam_time_naive()
    day_map = {
        0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday',
        4: 'friday', 5: 'saturday', 6: 'sunday'
    }
    today_day = day_map[today.weekday()]

    # Lấy lịch hôm nay
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).all()

    class_ids = [e.class_id for e in enrollments]

    today_schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id.in_(class_ids),
        ClassSchedule.day_of_week == today_day,
        ClassSchedule.is_active == True
    ).order_by(ClassSchedule.time_start).limit(5).all()

    # Exams stats: only class exams
    exams = ExamService.get_class_exams_for_student(student_id)
    now = get_vietnam_time_naive()
    exams_upcoming = 0
    exams_available = 0  # trong thời gian thi và chưa thi
    exams_completed = 0
    for exam in exams:
        results = ExamService.get_student_exam_result(exam.exam_id, student_id)
        attempts_used = len(results)
        if attempts_used >= 1:
            exams_completed += 1
        elif now < exam.start_time:
            exams_upcoming += 1
        elif now <= exam.end_time:
            exams_available += 1

    # Assignments stats: get all assignments (individual + class) - same logic as my_assignments
    from app.models.assignment import Assignment
    try:
        from app.models.training_video import TrainingVideo
        from app.models.manual_evaluation import ManualEvaluation
        from app.models.training_history import TrainingHistory
        from sqlalchemy import func, case
        from datetime import timedelta
    except Exception:
        TrainingVideo = None
        ManualEvaluation = None
        TrainingHistory = None
    
    # Get individual assignments
    individual = Assignment.query.filter_by(
        assigned_to_student=student_id,
        assignment_type='individual'
    ).all()
    
    # Get class assignments
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).all()
    class_ids = [e.class_id for e in enrollments]
    
    class_assignments = Assignment.query.filter(
        Assignment.assigned_to_class.in_(class_ids),
        Assignment.assignment_type == 'class'
    ).all() if class_ids else []
    
    # Combine all assignments (don't filter expired - show all)
    all_assignments = individual + class_assignments
    
    assignments_pending = 0
    assignments_completed = 0
    for a in all_assignments:
        submitted = None
        if TrainingVideo is not None:
            submitted = TrainingVideo.query.filter_by(
                student_id=student_id,
                assignment_id=a.assignment_id,
            ).first()
        if submitted:
            assignments_completed += 1
        else:
            assignments_pending += 1
    
    # Chart data: Score progression (30 days)
    score_timeline_labels = []
    score_timeline_values = []
    if TrainingVideo is not None and ManualEvaluation is not None:
        thirty_days_ago = today - timedelta(days=30)
        
        # Get all videos with evaluations in the last 30 days
        # Join with ManualEvaluation to ensure we only get videos with scores
        videos_with_scores = db.session.query(TrainingVideo, ManualEvaluation).join(
            ManualEvaluation, TrainingVideo.video_id == ManualEvaluation.video_id
        ).filter(
            TrainingVideo.student_id == student_id,
            TrainingVideo.uploaded_at >= thirty_days_ago
        ).order_by(TrainingVideo.uploaded_at).all()
        
        # Group by date and calculate average score
        from collections import defaultdict
        daily_scores = defaultdict(list)
        for video, evaluation in videos_with_scores:
            if evaluation and evaluation.overall_score is not None:
                date_str = video.uploaded_at.strftime('%d/%m')
                score = float(evaluation.overall_score)
                daily_scores[date_str].append(score)
        
        # Calculate average per day
        if daily_scores:
            for date_str in sorted(daily_scores.keys()):
                scores = daily_scores[date_str]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    score_timeline_labels.append(date_str)
                    score_timeline_values.append(round(avg_score, 1))
    
    # Chart data: Assignment status distribution
    status_distribution_labels = ['Đã nộp', 'Chưa nộp']
    status_distribution_values = [assignments_completed, assignments_pending]
    
    # Overall statistics
    total_videos = 0
    avg_score = 0.0
    if TrainingVideo is not None:
        total_videos = TrainingVideo.query.filter_by(student_id=student_id).count()
        if ManualEvaluation is not None:
            # Calculate average score from all manual evaluations
            avg_result = db.session.query(func.avg(ManualEvaluation.overall_score)).join(
                TrainingVideo, ManualEvaluation.video_id == TrainingVideo.video_id
            ).filter(TrainingVideo.student_id == student_id).scalar()
            if avg_result:
                avg_score = round(float(avg_result), 1)
    
    total_assignments = assignments_pending + assignments_completed

    return render_template('student/dashboard.html',
                         active_classes=active_classes,
                         completed_classes=completed_classes,
                         today_schedules=today_schedules,
                         exams_upcoming=exams_upcoming,
                         exams_available=exams_available,
                         exams_completed=exams_completed,
                         assignments_pending=assignments_pending,
                         assignments_completed=assignments_completed,
                         score_timeline_labels=score_timeline_labels,
                         score_timeline_values=score_timeline_values,
                         status_distribution_labels=status_distribution_labels,
                         status_distribution_values=status_distribution_values,
                         total_videos=total_videos,
                         avg_score=avg_score,
                         total_assignments=total_assignments)


@student_bp.route('/classes')
@login_required
@role_required('STUDENT')
def classes():
    """Danh sách tất cả lớp học của học viên"""
    student_id = session['user_id']

    # Lấy tất cả enrollments
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id
    ).order_by(ClassEnrollment.enrolled_at.desc()).all()

    return render_template('student/classes.html', enrollments=enrollments)


@student_bp.route('/classes/<int:class_id>')
@login_required
@role_required('STUDENT')
def class_detail(class_id: int):
    """Chi tiết lớp học"""
    student_id = session['user_id']

    # Kiểm tra học viên có trong lớp không
    enrollment = ClassEnrollment.query.filter_by(
        student_id=student_id,
        class_id=class_id
    ).first()

    if not enrollment:
        flash('Bạn không có quyền truy cập lớp này', 'error')
        return redirect(url_for('student.classes'))

    class_obj = Class.query.get(class_id)
    if not class_obj:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('student.classes'))

    # Lấy lịch học
    schedules = ClassSchedule.query.filter_by(
        class_id=class_id,
        is_active=True
    ).order_by(ClassSchedule.day_of_week, ClassSchedule.time_start).all()

    # Lấy danh sách học viên cùng lớp
    classmates = ClassEnrollment.query.filter_by(
        class_id=class_id,
        enrollment_status='active'
    ).filter(ClassEnrollment.student_id != student_id).all()

    return render_template('student/class_detail.html',
                         class_obj=class_obj,
                         enrollment=enrollment,
                         schedules=schedules,
                         classmates=classmates)


@student_bp.route('/schedules')
@login_required
@role_required('STUDENT')
def all_schedules():
    """Xem tất cả lịch học (theo tuần)"""
    student_id = session['user_id']

    # Lấy tất cả lớp đang học
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).all()

    class_ids = [e.class_id for e in enrollments]

    # Lấy tất cả lịch học
    schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id.in_(class_ids),
        ClassSchedule.is_active == True
    ).order_by(ClassSchedule.day_of_week, ClassSchedule.time_start).all()

    # Nhóm theo ngày
    schedule_by_day = {
        'monday': [],
        'tuesday': [],
        'wednesday': [],
        'thursday': [],
        'friday': [],
        'saturday': [],
        'sunday': []
    }

    for schedule in schedules:
        schedule_by_day[schedule.day_of_week].append(schedule)

    return render_template('student/schedules.html',
                         schedule_by_day=schedule_by_day)


# ============ ROUTINE VIEW (STUDENT) ============

@student_bp.route('/routines')
@login_required
@role_required('STUDENT')
def routines():
    # Read filters from query params
    level_filter = request.args.get('level')  # beginner | intermediate | advanced | ''
    weapon_filter = request.args.get('weapon_id', type=int)

    filters = {}
    if level_filter in ['beginner', 'intermediate', 'advanced']:
        filters['level'] = level_filter
    if weapon_filter:
        filters['weapon_id'] = weapon_filter

    routines = RoutineService.get_routines_for_student(session['user_id'], filters)
    weapons = RoutineService.get_all_weapons()
    return render_template('student/routines.html', routines=routines, weapons=weapons)


@student_bp.route('/routines/<int:routine_id>')
@login_required
@role_required('STUDENT')
def routine_detail(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or not routine.is_published:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('student.routines'))
    return render_template('student/routine_detail.html', routine=routine)


@student_bp.route('/my-assignments')
@login_required
@role_required('STUDENT')
def my_assignments():
    # Get all assignments (including expired) so students can see what they missed
    student_id = session['user_id']
    
    # Get individual assignments
    from app.models.assignment import Assignment
    from app.models.class_enrollment import ClassEnrollment
    from app.models.training_video import TrainingVideo
    
    individual = Assignment.query.filter_by(
        assigned_to_student=student_id,
        assignment_type='individual'
    ).all()
    
    # Get class assignments
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).all()
    class_ids = [e.class_id for e in enrollments]
    
    class_assignments = Assignment.query.filter(
        Assignment.assigned_to_class.in_(class_ids),
        Assignment.assignment_type == 'class'
    ).all() if class_ids else []
    
    # Combine all assignments (don't filter expired - show all)
    all_assignments = individual + class_assignments
    
    # Separate into pending and completed
    pending = []
    completed = []
    for assignment in all_assignments:
        submitted = TrainingVideo.query.filter_by(
            student_id=student_id,
            assignment_id=assignment.assignment_id,
        ).first()
        if submitted:
            completed.append({'assignment': assignment, 'video': submitted})
        else:
            pending.append(assignment)
    
    now = get_vietnam_time_naive()
    return render_template('student/my_assignments.html', pending=pending, completed=completed, now=now)


@student_bp.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('STUDENT')
def submit_assignment(assignment_id):
    """Nộp bài tập - Upload video"""
    
    # GET: Hiển thị form upload
    if request.method == 'GET':
        assignment = AssignmentService.get_assignment_by_id(assignment_id)
        
        if not assignment:
            flash('Không tìm thấy bài tập', 'error')
            return redirect(url_for('student.my_assignments'))
        
        # Kiểm tra quyền submit
        check = AssignmentService.can_submit(assignment_id, session['user_id'])
        if not check['can_submit']:
            flash(check['message'], 'error')
            return redirect(url_for('student.my_assignments'))
        
        return render_template('student/assignment_submit.html', assignment=assignment)
    
    # POST: Xử lý upload video
    if request.method == 'POST':
        # Kiểm tra quyền submit
        check = AssignmentService.can_submit(assignment_id, session['user_id'])
        
        if not check['can_submit']:
            flash(check['message'], 'error')
            return redirect(url_for('student.my_assignments'))
        
        # Validate file upload
        if 'video_file' not in request.files:
            flash('Không tìm thấy file video', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))
        
        video_file = request.files['video_file']
        
        if video_file.filename == '':
            flash('Chưa chọn file', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))
        
        # Kiểm tra định dạng file
        allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}
        file_ext = video_file.filename.rsplit('.', 1)[1].lower() if '.' in video_file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash(f'Định dạng không hợp lệ. Chỉ chấp nhận: {", ".join(allowed_extensions)}', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))
        
        try:
            # Lấy thông tin assignment
            assignment = AssignmentService.get_assignment_by_id(assignment_id)
            
            # Lưu video với assignment_id
            video = VideoService.save_video(
                file=video_file,
                student_id=session['user_id'],
                routine_id=assignment.routine_id,
                assignment_id=assignment_id,
                notes=request.form.get('notes', '')
            )
            
            # Chạy AI grading nếu được chọn trong assignment
            print(f"\n[Submit Assignment] Assignment ID: {assignment_id}, Grading Method: {assignment.grading_method}", flush=True)
            if assignment.grading_method in ['ai', 'both']:
                print(f"[Submit Assignment] Triggering AI grading for video {video.video_id}", flush=True)
                from app.services.ai_grading_service import AIGradingService
                AIGradingService.grade_async(video.video_id)
                flash('Nộp bài thành công! Hệ thống đang chấm điểm AI...', 'success')
            else:
                print(f"[Submit Assignment] Grading method is '{assignment.grading_method}', skipping AI grading", flush=True)
                flash('Nộp bài thành công!', 'success')
            
            return redirect(url_for('student.my_assignments'))
            
        except Exception as e:
            flash(f'Lỗi khi nộp bài: {str(e)}', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))


@student_bp.route('/my-exams')
@login_required
@role_required('STUDENT')
def my_exams():
    exams = ExamService.get_class_exams_for_student(session['user_id'])
    now = get_vietnam_time_naive()
    upcoming = []
    active = []  # Đang trong thời gian thi
    past = []
    
    for exam in exams:
        results = ExamService.get_student_exam_result(exam.exam_id, session['user_id'])
        attempts_used = len(results)
        
        # Check if can attempt: must be within time window AND have attempts left
        can_attempt = (
            attempts_used < exam.max_attempts and 
            now >= exam.start_time and 
            now <= exam.end_time
        )
        
        exam_info = {
            'exam': exam,
            'results': results,
            'attempts_used': attempts_used,
            'can_attempt': can_attempt,
        }
        
        # Phân loại exam theo thời gian
        if now < exam.start_time:
            # Chưa đến giờ thi
            upcoming.append(exam_info)
        elif now <= exam.end_time:
            # Đang trong thời gian thi (start_time <= now <= end_time)
            active.append(exam_info)
        else:
            # Đã hết hạn thi (now > end_time)
            past.append(exam_info)
    
    return render_template('student/my_exams.html', 
                         upcoming=upcoming, 
                         active=active,
                         past=past, 
                         now=now)



# ============ EXAM TAKING (THÊM MỚI) ============

@student_bp.route('/exams/<int:exam_id>/take', methods=['GET'])
@login_required
@role_required('STUDENT')
def take_exam(exam_id: int):
    """Trang làm bài thi"""
    # Lấy thông tin exam
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam or not exam.is_published:
        flash('Không tìm thấy bài kiểm tra hoặc chưa được xuất bản', 'error')
        return redirect(url_for('student.my_exams'))
    
    # Kiểm tra điều kiện vào thi
    can_take, message = ExamService.can_take_exam(exam_id, session['user_id'])
    if not can_take:
        flash(message, 'error')
        return redirect(url_for('student.my_exams'))
    
    # Lấy số lần đã thi
    results = ExamService.get_student_exam_result(exam_id, session['user_id'])
    attempt_number = len(results) + 1
    
    # Lấy video URL
    video_url = exam.get_video_url()
    
    return render_template(
        'student/take_exam.html',
        exam=exam,
        attempt_number=attempt_number,
        video_url=video_url
    )


@student_bp.route('/exams/<int:exam_id>/submit', methods=['POST'])
@login_required
@role_required('STUDENT')
def submit_exam(exam_id: int):
    """Nộp bài thi"""
    # Kiểm tra điều kiện
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam:
        flash('Không tìm thấy bài kiểm tra', 'error')
        return redirect(url_for('student.my_exams'))
    
    can_take, message = ExamService.can_take_exam(exam_id, session['user_id'])
    if not can_take:
        flash(message, 'error')
        return redirect(url_for('student.my_exams'))
    
    # Lấy video file
    if 'student_video' not in request.files:
        flash('Vui lòng ghi video làm bài', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))
    
    video_file = request.files['student_video']
    if not video_file or video_file.filename == '':
        flash('Vui lòng chọn video', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))
    
    # Validate video format
    allowed_extensions = {'mp4', 'avi', 'mov', 'webm'}
    file_ext = video_file.filename.rsplit('.', 1)[1].lower() if '.' in video_file.filename else ''
    
    if file_ext not in allowed_extensions:
        flash(f'Định dạng không hợp lệ. Chỉ chấp nhận: {", ".join(allowed_extensions)}', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))
    
    try:
        # Nộp bài và lưu kết quả
        result = ExamService.submit_exam_result(
            exam_id=exam_id,
            student_id=session['user_id'],
            video_file=video_file,
            notes=request.form.get('notes', '')
        )
        
        if result['success']:
            flash('Nộp bài thành công! Hệ thống đang chấm điểm...', 'success')
            return redirect(url_for('student.my_exams'))
        else:
            flash(result['message'], 'error')
            return redirect(url_for('student.take_exam', exam_id=exam_id))
            
    except Exception as e:
        flash(f'Lỗi khi nộp bài: {str(e)}', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))


@student_bp.route('/weapon-detect', methods=['GET', 'POST'])
@login_required
@role_required('STUDENT')
def weapon_detect():
    from app.services.ai_client_service import AIClientService
    from app.utils.storage_service import StorageService
    import uuid
    
    result = None
    error = None
    file_url = None
    file_type = None
    original_filename = None
    
    if request.method == 'POST':
        if 'file' not in request.files:
            error = 'Vui lòng chọn file video hoặc ảnh'
        else:
            file = request.files['file']
            if file.filename == '':
                error = 'Vui lòng chọn file'
            else:
                try:
                    filename = secure_filename(file.filename)
                    original_filename = filename
                    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                    
                    if ext not in ['mp4', 'avi', 'mov', 'jpg', 'jpeg', 'png']:
                        error = 'File không hợp lệ. Vui lòng chọn video (MP4, AVI, MOV) hoặc ảnh (JPG, PNG)'
                    else:
                        temp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as temp_file:
                                file.save(temp_file.name)
                                temp_path = temp_file.name
                            
                            detection_result = AIClientService.detect_weapon(temp_path)
                            
                            detected_weapon = detection_result.get('detected_weapon')
                            if detected_weapon is None:
                                detected_weapon = 'Không xác định'
                            
                            annotated_image_url = detection_result.get('annotated_image_url')
                            annotated_video_url = detection_result.get('annotated_video_url')
                            
                            result_image_url = None
                            result_video_url = None
                            
                            if ext in ['jpg', 'jpeg', 'png']:
                                file_type = 'image'
                                if annotated_image_url:
                                    result_image_url = annotated_image_url
                            else:
                                file_type = 'video'
                                if annotated_video_url:
                                    result_video_url = annotated_video_url
                            
                            unique_filename = f"{uuid.uuid4().hex}.{ext}"
                            try:
                                file_url = StorageService.upload_file_from_path(temp_path, folder='weapon_detect', filename=unique_filename)
                            except Exception:
                                file_url = None
                            
                            result = {
                                'detected_weapon': detected_weapon,
                                'confidence': detection_result.get('confidence', 0.0) or 0.0,
                                'detection_count': detection_result.get('detection_count', 0) or 0,
                                'total_samples': detection_result.get('total_samples', 0) or 1,
                                'all_detections': detection_result.get('all_detections', []),
                                'file_info': {
                                    'name': original_filename,
                                    'size': file.content_length or 0
                                },
                                'result_image_url': result_image_url,
                                'result_video_url': result_video_url
                            }
                            
                            files_to_delete = []
                            if file_url:
                                files_to_delete.append(file_url)
                            if result_image_url:
                                files_to_delete.append(result_image_url)
                            if result_video_url:
                                files_to_delete.append(result_video_url)
                            
                            if files_to_delete:
                                import threading
                                import time
                                
                                def delete_files_after_delay(urls, delay_seconds=300):
                                    time.sleep(delay_seconds)
                                    for url in urls:
                                        try:
                                            StorageService.delete_file(url)
                                        except Exception:
                                            pass
                                
                                thread = threading.Thread(target=delete_files_after_delay, args=(files_to_delete,))
                                thread.daemon = True
                                thread.start()
                        except Exception as e:
                            error = f'Lỗi khi nhận diện vũ khí: {str(e)}'
                            import traceback
                            traceback.print_exc()
                        finally:
                            if temp_path and os.path.exists(temp_path):
                                import time
                                max_retries = 5
                                for i in range(max_retries):
                                    try:
                                        os.remove(temp_path)
                                        break
                                    except (OSError, PermissionError) as e:
                                        if i < max_retries - 1:
                                            time.sleep(0.1)
                                        else:
                                            print(f"[WeaponDetect] Không thể xóa file {temp_path}: {e}", flush=True)
                            
                except Exception as e:
                    error = f'Lỗi khi xử lý file: {str(e)}'
                    import traceback
                    traceback.print_exc()
    
    return render_template('student/weapon_detect.html', 
                         result=result, 
                         error=error, 
                         file_url=file_url, 
                         file_type=file_type,
                         original_filename=original_filename)