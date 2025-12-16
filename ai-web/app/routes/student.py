from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from app.utils.decorators import login_required, role_required
from app.utils.helpers import get_vietnam_time, get_vietnam_time_naive
from app.models.class_enrollment import ClassEnrollment
from app.models.class_model import Class
from app.models.class_schedule import ClassSchedule
from app.models.user import User
from sqlalchemy import and_
from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService
from app.services.video_service import VideoService
from app.services.weapon_detection_service import WeaponDetectionService
from app.services.analytics_service import AnalyticsService
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

    # Assignments stats: only class assignments
    assignments = AssignmentService.get_active_class_assignments_for_student(student_id)
    try:
        from app.models.training_video import TrainingVideo
    except Exception:
        TrainingVideo = None
    assignments_pending = 0
    assignments_completed = 0
    for a in assignments:
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

    return render_template('student/dashboard.html',
                         active_classes=active_classes,
                         completed_classes=completed_classes,
                         today_schedules=today_schedules,
                         exams_upcoming=exams_upcoming,
                         exams_available=exams_available,
                         exams_completed=exams_completed,
                         assignments_pending=assignments_pending,
                         assignments_completed=assignments_completed)


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
    # Use the new method that filters out expired assignments
    assignments = AssignmentService.get_active_assignments_for_student(session['user_id'])
    from datetime import datetime
    pending = []
    completed = []
    for assignment in assignments:
        from app.models.training_video import TrainingVideo
        submitted = TrainingVideo.query.filter_by(
            student_id=session['user_id'],
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
        exam_info = {
            'exam': exam,
            'results': results,
            'attempts_used': len(results),
            'can_attempt': len(results) < exam.max_attempts and now < exam.end_time,
        }
        
        # Phân loại exam theo thời gian
        if now < exam.start_time:
            # Chưa đến giờ thi
            upcoming.append(exam_info)
        elif now <= exam.end_time:
            # Đang trong thời gian thi
            active.append(exam_info)
        else:
            # Đã hết hạn thi
            past.append(exam_info)
    
    return render_template('student/my_exams.html', 
                         upcoming=upcoming, 
                         active=active,
                         past=past, 
                         now=now)


# ============ ANALYTICS & GOALS ============

@student_bp.route('/analytics')
@login_required
@role_required('STUDENT')
def analytics():
    """Dashboard phân tích học viên"""
    student_id = session['user_id']
    
    # Base analytics from service
    overview = AnalyticsService.get_student_overview(student_id) or {}
    score_list = AnalyticsService.get_score_progression(student_id, days=30) or []
    completion_stats = AnalyticsService.get_routine_completion(student_id) or {}
    strengths_raw = AnalyticsService.get_strengths_weaknesses(student_id) or {}

    # Derive additional overview fields expected by template
    try:
        from app.models.training_video import TrainingVideo
    except Exception:
        TrainingVideo = None
    
    # avg_score preference: manual then AI
    avg_score = overview.get('avg_manual_score') or overview.get('avg_ai_score') or 0
    
    routines_practiced = 0
    practice_days = 0
    if TrainingVideo is not None:
        try:
            from sqlalchemy import func
            # distinct routines
            routines_practiced = (
                TrainingVideo.query
                .with_entities(func.count(func.distinct(TrainingVideo.routine_id)))
                .filter(TrainingVideo.student_id == student_id)
                .scalar() or 0
            )
            # distinct practice days
            distinct_days = (
                TrainingVideo.query
                .with_entities(func.date(TrainingVideo.uploaded_at))
                .filter(TrainingVideo.student_id == student_id)
                .distinct()
                .all()
            )
            practice_days = len(distinct_days)
        except Exception:
            pass
    
    overview_mapped = {
        **overview,
        'avg_score': round(float(avg_score), 1) if isinstance(avg_score, (int, float)) else 0,
        'routines_practiced': int(routines_practiced),
        'practice_days': int(practice_days),
    }
    
    # Build chart-friendly score data { dates: [...], scores: [...] }
    dates = []
    scores = []
    for item in score_list:
        score_val = item.get('manual_score') if item.get('manual_score') is not None else item.get('ai_score')
        if score_val is not None:
            dates.append(item.get('date'))
            # Normalize to percentage-like scale if needed
            scores.append(float(score_val))
    score_chart = { 'dates': dates, 'scores': scores }
    
    # Map completion stats to the template's expected list items
    completion_list = []
    if completion_stats:
        completion_list.append({
            'routine_name': 'Tất cả bài võ',
            'completion_rate': completion_stats.get('completion_rate', 0),
            'completed': completion_stats.get('completed', 0),
            'total': completion_stats.get('total_routines', 0),
        })
    
    # Synthesize strengths/weaknesses lists from technique/posture/timing
    sw_mapped = { 'strengths': [], 'weaknesses': [] }
    if strengths_raw:
        crits = [
            { 'criteria_name': 'Kỹ thuật', 'key': 'technique', 'avg_score': strengths_raw.get('technique') },
            { 'criteria_name': 'Tư thế', 'key': 'posture', 'avg_score': strengths_raw.get('posture') },
            { 'criteria_name': 'Nhịp điệu', 'key': 'timing', 'avg_score': strengths_raw.get('timing') },
        ]
        for c in crits:
            val = c.get('avg_score')
            if val is None:
                continue
            entry = { 'criteria_name': c['criteria_name'], 'avg_score': round(float(val), 1) }
            # Simple heuristic thresholds
            if val >= 70:
                sw_mapped['strengths'].append(entry)
            elif val <= 50:
                sw_mapped['weaknesses'].append(entry)
    
    return render_template(
        'student/analytics.html',
        overview=overview_mapped,
        score_data=score_chart,
        completion=completion_list,
        strengths=sw_mapped
    )

 


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
                            
                            annotated_image_b64 = detection_result.get('annotated_image')
                            annotated_video_b64 = detection_result.get('annotated_video')
                            
                            result_image_url = None
                            result_video_url = None
                            
                            if ext in ['jpg', 'jpeg', 'png']:
                                file_type = 'image'
                                if annotated_image_b64:
                                    try:
                                        import base64
                                        image_bytes = base64.b64decode(annotated_image_b64)
                                        result_image_path = temp_path.replace(f'.{ext}', f'_result.{ext}')
                                        with open(result_image_path, 'wb') as f:
                                            f.write(image_bytes)
                                        
                                        result_image_filename = f"{uuid.uuid4().hex}_result.{ext}"
                                        result_image_url = StorageService.upload_file_from_path(result_image_path, folder='weapon_detect', filename=result_image_filename)
                                        
                                        if os.path.exists(result_image_path):
                                            os.remove(result_image_path)
                                    except Exception:
                                        pass
                            else:
                                file_type = 'video'
                                if annotated_video_b64:
                                    try:
                                        import base64
                                        video_bytes = base64.b64decode(annotated_video_b64)
                                        result_video_path = temp_path.replace(f'.{ext}', f'_result.{ext}')
                                        with open(result_video_path, 'wb') as f:
                                            f.write(video_bytes)
                                        
                                        result_video_filename = f"{uuid.uuid4().hex}_result.{ext}"
                                        result_video_url = StorageService.upload_file_from_path(result_video_path, folder='weapon_detect', filename=result_video_filename)
                                        
                                        if os.path.exists(result_video_path):
                                            os.remove(result_video_path)
                                    except Exception:
                                        pass
                            
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