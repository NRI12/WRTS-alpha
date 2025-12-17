from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app, request
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from app.services.class_service import ClassService
from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService
from app.utils.decorators import login_required, role_required
from app.utils.storage_service import StorageService
from app.forms.class_forms import ClassCreateForm, ClassEditForm, EnrollStudentForm
from app.forms.routine_forms import RoutineCreateForm, RoutineEditForm
from app.forms.assignment_forms import AssignmentCreateForm, AssignmentEditForm
from app.forms.exam_forms import ExamCreateForm
from app.forms.class_forms import ClassCreateForm, ClassEditForm, EnrollStudentForm
from app.forms.schedule_forms import ScheduleForm
from app.forms.evaluation_forms import ManualEvaluationForm
from app.services.schedule_service import ScheduleService
from app.models.class_enrollment import ClassEnrollment
from app.models import db
from app.models.assignment import Assignment
from app.models.manual_evaluation import ManualEvaluation
from app.models.training_video import TrainingVideo
from sqlalchemy import func


instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')


@instructor_bp.route('/dashboard')
@login_required
@role_required('INSTRUCTOR')
def dashboard():
    instructor_id = session['user_id']
    
    approved_classes = ClassService.get_approved_classes_by_instructor(instructor_id)
    my_proposals = ClassService.get_my_proposals(instructor_id)
    
    assignments_data = AssignmentService.get_assignments_with_stats(instructor_id)
    assignment_stats = assignments_data['stats']
    recent_assignments = assignments_data['assignments'][:5] if assignments_data['assignments'] else []
    
    from app.utils.helpers import get_vietnam_time_naive
    exams = ExamService.get_exams_by_instructor(instructor_id)
    now = get_vietnam_time_naive()
    upcoming_exams = [e for e in exams if e.end_time and e.end_time > now][:5]
    
    pending_count = assignment_stats.get('submitted', 0)
    
    from app.models.manual_evaluation import ManualEvaluation
    from app.models.training_video import TrainingVideo
    from sqlalchemy import func
    avg_score_result = db.session.query(func.avg(ManualEvaluation.overall_score)).join(
        TrainingVideo, ManualEvaluation.video_id == TrainingVideo.video_id
    ).join(
        Assignment, TrainingVideo.assignment_id == Assignment.assignment_id
    ).filter(
        Assignment.assigned_by == instructor_id
    ).scalar()
    
    avg_score = round(float(avg_score_result), 1) if avg_score_result else None
    
    from datetime import timedelta
    from collections import defaultdict
    from sqlalchemy import func, and_
    
    score_timeline_data = defaultdict(list)
    
    evaluations = db.session.query(
        ManualEvaluation.overall_score,
        ManualEvaluation.evaluated_at
    ).join(
        TrainingVideo, ManualEvaluation.video_id == TrainingVideo.video_id
    ).join(
        Assignment, TrainingVideo.assignment_id == Assignment.assignment_id
    ).filter(
        and_(
            Assignment.assigned_by == instructor_id,
            ManualEvaluation.evaluation_method == 'manual',
            ManualEvaluation.evaluated_at >= datetime.utcnow() - timedelta(days=30)
        )
    ).order_by(
        ManualEvaluation.evaluated_at
    ).all()
    
    for eval in evaluations:
        eval_date = eval.evaluated_at.date() if hasattr(eval.evaluated_at, 'date') else eval.evaluated_at
        if isinstance(eval_date, str):
            from datetime import datetime as dt
            try:
                eval_date = dt.strptime(eval_date, '%Y-%m-%d').date()
            except:
                continue
        score_timeline_data[eval_date].append(float(eval.overall_score))
    
    score_timeline_labels = []
    score_timeline_values = []
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=29-i)).date()
        date_str = date.strftime('%d/%m')
        score_timeline_labels.append(date_str)
        if date in score_timeline_data:
            avg_score = sum(score_timeline_data[date]) / len(score_timeline_data[date])
            score_timeline_values.append(round(avg_score, 1))
        else:
            score_timeline_values.append(None)
    
    status_distribution_labels = ['Chưa nộp', 'Đã nộp', 'Đã chấm']
    status_distribution_values = [
        assignment_stats.get('pending', 0),
        assignment_stats.get('submitted', 0),
        assignment_stats.get('graded', 0)
    ]
    
    return render_template('instructor/dashboard.html', 
                         approved_classes=approved_classes, 
                         my_proposals=my_proposals,
                         assignment_stats=assignment_stats,
                         recent_assignments=recent_assignments,
                         upcoming_exams=upcoming_exams,
                         pending_count=pending_count,
                         avg_score=avg_score,
                         score_timeline_labels=score_timeline_labels,
                         score_timeline_values=score_timeline_values,
                         status_distribution_labels=status_distribution_labels,
                         status_distribution_values=status_distribution_values)


@instructor_bp.route('/classes')
@login_required
@role_required('INSTRUCTOR')
def classes():
    classes = ClassService.get_approved_classes_by_instructor(session['user_id'])
    return render_template('instructor/classes.html', classes=classes)


@instructor_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_class():
    flash('Bạn không có quyền tạo lớp trực tiếp. Vui lòng gửi đề xuất lớp học.', 'error')
    return redirect(url_for('instructor.propose_class'))


@instructor_bp.route('/classes/<int:class_id>')
@login_required
@role_required('INSTRUCTOR')
def class_detail(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    if class_obj.instructor_id != session['user_id']:
        flash('Bạn không có quyền truy cập lớp này', 'error')
        return redirect(url_for('instructor.classes'))

    enrollments = ClassService.get_enrolled_students(class_id)

    # Fetch recent assignments with stats
    assignments_data = AssignmentService.get_recent_class_assignments(class_id, limit=5)
    recent_assignments = assignments_data['assignments']
    assignment_stats = assignments_data['stats']

    # Fetch upcoming and recent exams
    upcoming_exams = ExamService.get_upcoming_class_exams(class_id, limit=3)
    recent_exams = ExamService.get_recent_class_exams(class_id, limit=3)

    return render_template('instructor/class_detail.html', 
                         class_obj=class_obj, 
                         enrollments=enrollments, 
                         recent_assignments=recent_assignments,
                         assignment_stats=assignment_stats,
                         upcoming_exams=upcoming_exams,
                         recent_exams=recent_exams,
                         ClassService=ClassService)


@instructor_bp.route('/proposals')
@login_required
@role_required('INSTRUCTOR')
def my_proposals():
    proposals = ClassService.get_my_proposals(session['user_id'])
    return render_template('instructor/my_proposals.html', proposals=proposals)


@instructor_bp.route('/classes/propose', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def propose_class():
    form = ClassCreateForm()

    if form.is_submitted() and not form.validate():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')

    if form.validate_on_submit():
        data = {
            'class_code': form.class_code.data,
            'class_name': form.class_name.data,
            'description': form.description.data,
            'level': form.level.data,
            'max_students': form.max_students.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
        }
        result = ClassService.create_class_proposal(data, session['user_id'])
        if result['success']:
            flash('Đề xuất lớp học thành công! Vui lòng chờ Ban quản lý duyệt.', 'success')
            return redirect(url_for('instructor.my_proposals'))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/class_propose.html', form=form)
@instructor_bp.route('/classes/<int:class_id>/schedules')
@login_required
@role_required('INSTRUCTOR')
def class_schedules(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    schedules = ScheduleService.get_schedules_by_class(class_id)
    return render_template('instructor/class_schedules.html', class_obj=class_obj, schedules=schedules)


@instructor_bp.route('/classes/<int:class_id>/schedules/add', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def add_schedule(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    form = ScheduleForm()
    if form.validate_on_submit():
        data = {
            'day_of_week': form.day_of_week.data,
            'time_start': form.time_start.data,
            'time_end': form.time_end.data,
            'location': form.location.data,
            'notes': form.notes.data,
            'is_active': form.is_active.data,
        }
        result = ScheduleService.create_schedule(class_id, data)
        if result['success']:
            flash('Thêm lịch học thành công!', 'success')
            return redirect(url_for('instructor.class_schedules', class_id=class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/schedule_add.html', form=form, class_obj=class_obj)


@instructor_bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_schedule(schedule_id: int):
    schedule = ScheduleService.get_schedule_by_id(schedule_id)
    if not schedule or schedule.class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lịch học', 'error')
        return redirect(url_for('instructor.classes'))

    form = ScheduleForm(obj=schedule)
    if form.validate_on_submit():
        data = {
            'day_of_week': form.day_of_week.data,
            'time_start': form.time_start.data,
            'time_end': form.time_end.data,
            'location': form.location.data,
            'notes': form.notes.data,
            'is_active': form.is_active.data,
        }
        result = ScheduleService.update_schedule(schedule_id, data)
        if result['success']:
            flash('Cập nhật lịch học thành công!', 'success')
            return redirect(url_for('instructor.class_schedules', class_id=schedule.class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/schedule_edit.html', form=form, schedule=schedule)


@instructor_bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_schedule(schedule_id: int):
    schedule = ScheduleService.get_schedule_by_id(schedule_id)
    if not schedule or schedule.class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lịch học', 'error')
        return redirect(url_for('instructor.classes'))

    class_id = schedule.class_id
    result = ScheduleService.delete_schedule(schedule_id)
    if result['success']:
        flash('Xóa lịch học thành công!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('instructor.class_schedules', class_id=class_id))


@instructor_bp.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_class(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    form = ClassEditForm(obj=class_obj)
    enrollments = ClassService.get_enrolled_students(class_id)

    if form.validate_on_submit():
        data = {
            'class_code': form.class_code.data,
            'class_name': form.class_name.data,
            'description': form.description.data,
            'level': form.level.data,
            'max_students': form.max_students.data,
            'end_date': form.end_date.data,
            'is_active': form.is_active.data,
        }

        result = ClassService.update_class(class_id, data)
        if result['success']:
            flash('Cập nhật lớp học thành công!', 'success')
            return redirect(url_for('instructor.class_detail', class_id=class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/class_edit.html', form=form, class_obj=class_obj, enrollments=enrollments)


@instructor_bp.route('/classes/<int:class_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_class(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    result = ClassService.delete_class(class_id)
    if result['success']:
        flash('Xóa lớp học thành công!', 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('instructor.classes'))


@instructor_bp.route('/classes/<int:class_id>/students/add', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def add_student(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    form = EnrollStudentForm()
    available_students = ClassService.get_available_students(class_id)
    form.student_id.choices = [(0, '-- Chọn học viên --')] + [
        (s.user_id, f'{s.full_name} ({s.username})') for s in available_students
    ]
    form.student_ids.choices = [
        (s.user_id, f'{s.full_name} ({s.username})') for s in available_students
    ]
    enrollments = ClassService.get_enrolled_students(class_id)

    if form.validate_on_submit():
        student_ids = form.student_ids.data if form.student_ids.data else []
        if form.student_id.data and form.student_id.data != 0:
            student_ids.append(form.student_id.data)
        
        if not student_ids:
            flash('Vui lòng chọn ít nhất một học viên', 'error')
        elif len(student_ids) == 1:
            result = ClassService.enroll_student(class_id, student_ids[0], form.notes.data)
            if result['success']:
                flash('Thêm học viên thành công!', 'success')
                return redirect(url_for('instructor.class_detail', class_id=class_id))
            else:
                flash(result['message'], 'error')
        else:
            result = ClassService.enroll_multiple_students(class_id, student_ids, form.notes.data)
            if result['success']:
                flash(result['message'], 'success')
                if result['failed_count'] > 0:
                    flash(f'{result["failed_count"]} học viên không thể thêm', 'warning')
                return redirect(url_for('instructor.class_detail', class_id=class_id))
            else:
                flash(result['message'], 'error')

    return render_template('instructor/class_add_student.html', 
                         form=form, 
                         class_obj=class_obj, 
                         enrollments=enrollments,
                         available_students=available_students)


@instructor_bp.route('/enrollments/<int:enrollment_id>/remove', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def remove_student(enrollment_id: int):
    access_result = ClassService.verify_enrollment_access(enrollment_id, session['user_id'])
    if not access_result['success']:
        flash(access_result['message'], 'error')
        return redirect(url_for('instructor.classes'))

    enrollment = access_result['enrollment']
    class_id = enrollment.class_id
    result = ClassService.remove_student(enrollment_id)

    if result['success']:
        flash('Xóa học viên khỏi lớp thành công!', 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('instructor.class_detail', class_id=class_id))



@instructor_bp.route('/routines')
@login_required
@role_required('INSTRUCTOR')
def routines():
    level_filter = request.args.get('level')
    weapon_filter = request.args.get('weapon_id', type=int)
    status_filter = request.args.get('status')

    filters = {}
    if level_filter in ['beginner', 'intermediate', 'advanced']:
        filters['level'] = level_filter
    if weapon_filter:
        filters['weapon_id'] = weapon_filter
    if status_filter == 'published':
        filters['is_published'] = True
    elif status_filter == 'draft':
        filters['is_published'] = False

    routines = RoutineService.get_routines_by_instructor(session['user_id'], filters)
    weapons = RoutineService.get_all_weapons()
    return render_template(
        'instructor/routines.html',
        routines=routines,
        weapons=weapons,
        level_filter=level_filter or '',
        weapon_filter=weapon_filter or '',
        status_filter=status_filter or ''
    )

@instructor_bp.route('/routines/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_routine():
    form = RoutineCreateForm()
    weapons = RoutineService.get_all_weapons()
    form.weapon_id.choices = [(0, '-- Chọn binh khí --')] + [(w.weapon_id, w.weapon_name_vi) for w in weapons]
    
    if request.method == 'POST':
        print("=" * 50)
        print("REQUEST FILES:")
        print(request.files)
        print(f"Keys: {list(request.files.keys())}")
        print("FORM DATA:")
        print(f"reference_video_url: {form.reference_video_url.data}")
        print(f"reference_video_file.data: {form.reference_video_file.data}")
        print(f"reference_video_file.raw_data: {form.reference_video_file.raw_data}")
        print("=" * 50)
    
    if form.validate_on_submit():
        video_url = None
        
        if form.reference_video_file.data:
            video_file = form.reference_video_file.data
            filename = secure_filename(video_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            
            try:
                video_url = StorageService.upload_file(video_file, folder='routines', filename=unique_filename)
            except Exception as e:
                flash(f'Lỗi khi upload video: {str(e)}', 'error')
                return render_template('instructor/routine_create.html', form=form)
            
        elif form.reference_video_url.data:
            video_url = form.reference_video_url.data
        
        data = {
            'routine_code': form.routine_code.data,
            'routine_name': form.routine_name.data,
            'description': form.description.data,
            'weapon_id': form.weapon_id.data,
            'level': form.level.data,
            'difficulty_score': form.difficulty_score.data,
            'total_moves': form.total_moves.data,
            'pass_threshold': form.pass_threshold.data,
            'reference_video_url': video_url
        }
        
        result = RoutineService.create_routine(data, session['user_id'])
        if result['success']:
            flash('Tạo bài võ thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=result['routine'].routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/routine_create.html', form=form)


@instructor_bp.route('/routines/<int:routine_id>')
@login_required
@role_required('INSTRUCTOR')
def routine_detail(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    return render_template('instructor/routine_detail.html', routine=routine)


@instructor_bp.route('/routines/<int:routine_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_routine(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    form = RoutineEditForm(obj=routine)
    weapons = RoutineService.get_all_weapons()
    form.weapon_id.choices = [(w.weapon_id, w.weapon_name_vi) for w in weapons]
    
    if form.validate_on_submit():
        video_url = routine.reference_video_url
        
        if form.reference_video_file.data:
            video_file = form.reference_video_file.data
            filename = secure_filename(video_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            
            try:
                video_url = StorageService.upload_file(video_file, folder='routines', filename=unique_filename)
            except Exception as e:
                flash(f'Lỗi khi upload video: {str(e)}', 'error')
                return render_template('instructor/routine_edit.html', form=form, routine=routine)
            
        elif form.reference_video_url.data:
            video_url = form.reference_video_url.data
        
        data = {
            'routine_code': form.routine_code.data,
            'routine_name': form.routine_name.data,
            'description': form.description.data,
            'weapon_id': form.weapon_id.data,
            'level': form.level.data,
            'difficulty_score': form.difficulty_score.data,
            'total_moves': form.total_moves.data,
            'pass_threshold': form.pass_threshold.data,
            'reference_video_url': video_url
        }
        
        result = RoutineService.update_routine(routine_id, data, session['user_id'])
        if result['success']:
            flash('Cập nhật bài võ thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/routine_edit.html', form=form, routine=routine)


@instructor_bp.route('/routines/<int:routine_id>/publish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def publish_routine(routine_id: int):
    result = RoutineService.publish_routine(routine_id, session['user_id'])
    flash('Đã xuất bản bài võ!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/unpublish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def unpublish_routine(routine_id: int):
    result = RoutineService.unpublish_routine(routine_id, session['user_id'])
    flash('Đã gỡ xuất bản bài võ!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_routine(routine_id: int):
    result = RoutineService.delete_routine(routine_id, session['user_id'])
    if result['success']:
        flash('Xóa bài võ thành công!', 'success')
        return redirect(url_for('instructor.routines'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('instructor.routine_detail', routine_id=routine_id))



@instructor_bp.route('/assignments')
@login_required
@role_required('INSTRUCTOR')
def assignments():
    assignment_type = request.args.get('assignment_type')
    priority = request.args.get('priority')

    filters = {}
    if assignment_type in ['individual', 'class']:
        filters['assignment_type'] = assignment_type
    if priority in ['low', 'normal', 'high', 'urgent']:
        filters['priority'] = priority

    assignments_data = AssignmentService.get_assignments_with_stats(session['user_id'], filters)
    assignments = assignments_data['assignments']
    assignment_stats = assignments_data['assignment_stats']
    stats = assignments_data['stats']

    return render_template(
        'instructor/assignments.html',
        assignments=assignments,
        assignment_type=assignment_type or '',
        priority=priority or '',
        stats=stats,
        assignment_stats=assignment_stats,
    )


@instructor_bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_assignment():
    form = AssignmentCreateForm()
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    form_data = ClassService.get_students_for_assignment_form(session['user_id'])
    form.assigned_to_student.choices = [(0, '-- Chọn học viên --')] + [(s.user_id, s.full_name) for s in form_data['students']]
    form.assigned_to_class.choices = [(0, '-- Chọn lớp --')] + [(c.class_id, c.class_name) for c in form_data['classes']]
    
    # Auto-fill class_id from query parameter
    class_id_param = request.args.get('class_id', type=int)
    prefill_data = AssignmentService.get_form_prefill_data_for_class(class_id_param, session['user_id'])
    if prefill_data:
        form.assignment_type.data = prefill_data['assignment_type']
        form.assigned_to_class.data = prefill_data['assigned_to_class']
    if form.validate_on_submit():
        instructor_video_url = None
        
        if form.instructor_video_file.data:
            try:
                video_file = form.instructor_video_file.data
                filename = secure_filename(video_file.filename)
                
                file_size = len(video_file.read())
                video_file.seek(0)
                
                max_size = current_app.config.get('MAX_VIDEO_SIZE', 100 * 1024 * 1024)
                if file_size > max_size:
                    max_size_mb = max_size // (1024 * 1024)
                    flash(f'File video quá lớn! Vui lòng chọn file nhỏ hơn {max_size_mb}MB.', 'error')
                    return render_template('instructor/assignment_create.html', form=form)
                
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                instructor_video_url = StorageService.upload_file(video_file, folder='assignments', filename=unique_filename)
                
            except Exception as e:
                flash(f'Lỗi khi upload video: {str(e)}', 'error')
                return render_template('instructor/assignment_create.html', form=form)
            
        elif form.instructor_video_url.data:
            instructor_video_url = form.instructor_video_url.data
        
        if not instructor_video_url:
            flash('Vui lòng upload video demo hoặc nhập link video!', 'error')
            return render_template('instructor/assignment_create.html', form=form)
        
        data = {
            'routine_id': form.routine_id.data,
            'assignment_type': form.assignment_type.data,
            'assigned_to_student': form.assigned_to_student.data if form.assignment_type.data == 'individual' else None,
            'assigned_to_class': form.assigned_to_class.data if form.assignment_type.data == 'class' else None,
            'deadline': form.deadline.data,
            'instructions': form.instructions.data,
            'priority': form.priority.data,
            'is_mandatory': form.is_mandatory.data,
            'instructor_video_url': instructor_video_url,
            'grading_method': form.grading_method.data
        }
        
        result = AssignmentService.create_assignment(data, session['user_id'])
        if result['success']:
            flash('Gán bài tập thành công!', 'success')
            return redirect(url_for('instructor.assignments'))
        else:
            flash(result['message'], 'error')
    return render_template('instructor/assignment_create.html', form=form)


@instructor_bp.route('/assignments/<int:assignment_id>')
@login_required
@role_required('INSTRUCTOR')
def assignment_detail(assignment_id: int):
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    if not assignment or assignment.assigned_by != session['user_id']:
        flash('Không tìm thấy bài tập', 'error')
        return redirect(url_for('instructor.assignments'))
    status_list = AssignmentService.get_submission_status(assignment_id)
    return render_template('instructor/assignment_detail.html', assignment=assignment, status_list=status_list)


@instructor_bp.route('/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_assignment(assignment_id: int):
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    if not assignment or assignment.assigned_by != session['user_id']:
        flash('Không tìm thấy bài tập', 'error')
        return redirect(url_for('instructor.assignments'))
    
    form = AssignmentEditForm(obj=assignment)
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    form_data = ClassService.get_students_for_assignment_form(session['user_id'])
    form.assigned_to_student.choices = [(0, '-- Chọn học viên --')] + [(s.user_id, s.full_name) for s in form_data['students']]
    form.assigned_to_class.choices = [(0, '-- Chọn lớp --')] + [(c.class_id, c.class_name) for c in form_data['classes']]
    
    if form.validate_on_submit():
        instructor_video_url = assignment.instructor_video_url
        
        if form.instructor_video_file.data:
            video_file = form.instructor_video_file.data
            filename = secure_filename(video_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'mp4'
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            
            try:
                instructor_video_url = StorageService.upload_file(video_file, folder='assignments', filename=unique_filename)
            except Exception as e:
                flash(f'Lỗi khi upload video: {str(e)}', 'error')
                return render_template('instructor/assignment_edit.html', form=form, assignment=assignment)
        
        elif form.instructor_video_url.data:
            instructor_video_url = form.instructor_video_url.data
        
        data = {
            'routine_id': form.routine_id.data,
            'assignment_type': form.assignment_type.data,
            'assigned_to_student': form.assigned_to_student.data if form.assignment_type.data == 'individual' else None,
            'assigned_to_class': form.assigned_to_class.data if form.assignment_type.data == 'class' else None,
            'deadline': form.deadline.data,
            'instructions': form.instructions.data,
            'priority': form.priority.data,
            'is_mandatory': form.is_mandatory.data,
            'grading_method': form.grading_method.data,
        }
        
        if instructor_video_url:
            data['instructor_video_url'] = instructor_video_url
        
        result = AssignmentService.update_assignment(assignment_id, data, session['user_id'])
        if result['success']:
            flash('Cập nhật bài tập thành công!', 'success')
            return redirect(url_for('instructor.assignment_detail', assignment_id=assignment_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/assignment_edit.html', form=form, assignment=assignment)


@instructor_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_assignment(assignment_id: int):
    result = AssignmentService.delete_assignment(assignment_id, session['user_id'])
    flash('Xóa bài tập thành công!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.assignments'))


@instructor_bp.route('/assignments/delete-bulk', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_assignments_bulk():
    assignment_ids = request.form.getlist('assignment_ids')
    
    if not assignment_ids:
        flash('Vui lòng chọn ít nhất một bài tập để xóa', 'error')
        return redirect(url_for('instructor.assignments'))
    
    success_count = 0
    error_count = 0
    
    for assignment_id_str in assignment_ids:
        try:
            assignment_id = int(assignment_id_str)
            result = AssignmentService.delete_assignment(assignment_id, session['user_id'])
            if result['success']:
                success_count += 1
            else:
                error_count += 1
        except (ValueError, TypeError):
            error_count += 1
    
    if success_count > 0:
        flash(f'Đã xóa thành công {success_count} bài tập', 'success')
    if error_count > 0:
        flash(f'Không thể xóa {error_count} bài tập', 'error')
    
    return redirect(url_for('instructor.assignments'))



@instructor_bp.route('/exams')
@login_required
@role_required('INSTRUCTOR')
def exams():
    exams = ExamService.get_exams_by_instructor(session['user_id'])
    return render_template('instructor/exams.html', exams=exams)


@instructor_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_exam():
    form = ExamCreateForm()
    
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    classes = ClassService.get_classes_by_instructor(session['user_id'])
    form.class_id.choices = [(0, '-- Không chọn (tất cả) --')] + [(c.class_id, c.class_name) for c in classes]
    
    # Auto-fill class_id from query parameter
    class_id_param = request.args.get('class_id', type=int)
    prefill_data = ExamService.get_form_prefill_data_for_class(class_id_param, session['user_id'])
    if prefill_data:
        form.class_id.data = prefill_data['class_id']
    
    if form.validate_on_submit():
        data = {
            'exam_code': form.exam_code.data,
            'exam_name': form.exam_name.data,
            'description': form.description.data,
            'class_id': form.class_id.data if form.class_id.data else None,
            'routine_id': form.routine_id.data if form.routine_id.data else None,
            'exam_type': form.exam_type.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'pass_score': form.pass_score.data,
            'video_source': form.video_source.data,
        }
        
        video_file = form.reference_video.data if form.video_source.data == 'upload' else None
        
        result = ExamService.create_exam(data, session['user_id'], video_file)
        
        if result['success']:
            flash('Tạo bài kiểm tra thành công! (Trạng thái: Nháp)', 'success')
            return redirect(url_for('instructor.exam_detail', exam_id=result['exam'].exam_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/exam_create.html', form=form)


@instructor_bp.route('/exams/<int:exam_id>')
@login_required
@role_required('INSTRUCTOR')
def exam_detail(exam_id: int):
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam or exam.instructor_id != session['user_id']:
        flash('Không tìm thấy bài kiểm tra', 'error')
        return redirect(url_for('instructor.exams'))
    results = ExamService.get_exam_results(exam_id)
    return render_template('instructor/exam_detail.html', exam=exam, results=results)


@instructor_bp.route('/exams/<int:exam_id>/publish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def publish_exam(exam_id: int):
    result = ExamService.publish_exam(exam_id, session['user_id'])
    flash('Đã xuất bản bài kiểm tra!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.exam_detail', exam_id=exam_id))


@instructor_bp.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_exam(exam_id: int):
    form_data_result = ExamService.get_edit_form_data(exam_id, session['user_id'])
    if not form_data_result['success']:
        flash(form_data_result['message'], 'error')
        return redirect(url_for('instructor.exams'))
    
    exam = form_data_result['exam']
    routines = form_data_result['routines']
    classes = form_data_result['classes']
    
    from app.forms.exam_forms import ExamCreateForm
    form = ExamCreateForm(obj=exam)
    
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    form.class_id.choices = [(0, '-- Không chọn (tất cả) --')] + [(c.class_id, c.class_name) for c in classes]
    
    form.video_source.data = form_data_result['video_source']
    if form_data_result.get('routine_id'):
        form.routine_id.data = form_data_result['routine_id']
    
    if form.validate_on_submit():
        data = {
            'exam_code': form.exam_code.data,
            'exam_name': form.exam_name.data,
            'description': form.description.data,
            'class_id': form.class_id.data if form.class_id.data else None,
            'routine_id': form.routine_id.data if form.routine_id.data else None,
            'exam_type': form.exam_type.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'pass_score': form.pass_score.data,
            'video_source': form.video_source.data,
        }
        
        video_file = form.reference_video.data if form.video_source.data == 'upload' and form.reference_video.data else None
        
        result = ExamService.update_exam(exam_id, data, session['user_id'], video_file)
        
        if result['success']:
            flash('Cập nhật bài kiểm tra thành công!', 'success')
            return redirect(url_for('instructor.exam_detail', exam_id=exam_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/exam_edit.html', form=form, exam=exam)


@instructor_bp.route('/exams/<int:exam_id>/results/<int:result_id>/grade', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def grade_exam_result(exam_id: int, result_id: int):
    access_result = ExamService.verify_exam_result_access(result_id, session['user_id'])
    if not access_result['success']:
        flash(access_result['message'], 'error')
        return redirect(url_for('instructor.exam_detail', exam_id=exam_id))
    
    result = access_result['result']
    exam = access_result['exam']
    
    if not result.video_id:
        flash('Kết quả này chưa có video', 'error')
        return redirect(url_for('instructor.exam_detail', exam_id=exam_id))
    
    from app.services.video_service import VideoService
    from app.services.evaluation_service import EvaluationService
    from app.forms.evaluation_forms import ManualEvaluationForm
    
    video_data = VideoService.get_video_with_analysis(result.video_id)
    if not video_data:
        flash('Không tìm thấy video', 'error')
        return redirect(url_for('instructor.exam_detail', exam_id=exam_id))
    
    video = video_data['video']
    
    reference_video_url = None
    video_source = ""
    
    if exam.video_upload_method == 'routine' and exam.routine and exam.routine.reference_video_url:
        reference_video_url = exam.routine.reference_video_url
        video_source = f"Video mẫu: {exam.routine.routine_name}"
    elif exam.video_upload_method == 'upload' and exam.reference_video_path:
        reference_video_url = exam.get_video_url()
        video_source = "Video mẫu bài kiểm tra"
    
    existing_eval = EvaluationService.get_evaluation_for_instructor(video.video_id, session['user_id'])
    
    from app.models.manual_evaluation import ManualEvaluation
    ai_eval = ManualEvaluation.query.filter_by(
        video_id=video.video_id,
        evaluation_method='ai'
    ).first()
    
    if request.method == 'GET' and existing_eval:
        form = ManualEvaluationForm(
            overall_score=existing_eval.overall_score,
            technique_score=existing_eval.technique_score,
            posture_score=existing_eval.posture_score,
            spirit_score=existing_eval.spirit_score,
            strengths=existing_eval.strengths,
            improvements_needed=existing_eval.improvements_needed,
            comments=existing_eval.comments,
            is_passed=existing_eval.is_passed,
        )
    else:
        form = ManualEvaluationForm()
        if ai_eval:
            form.overall_score.data = ai_eval.overall_score
            form.technique_score.data = ai_eval.technique_score
            form.posture_score.data = ai_eval.posture_score
            form.spirit_score.data = ai_eval.spirit_score
    
    if form.validate_on_submit():
        data = {
            'overall_score': form.overall_score.data,
            'technique_score': form.technique_score.data,
            'posture_score': form.posture_score.data,
            'spirit_score': form.spirit_score.data,
            'strengths': form.strengths.data,
            'improvements_needed': form.improvements_needed.data,
            'comments': form.comments.data,
            'is_passed': form.is_passed.data,
            'evaluation_method': 'manual'
        }
        
        if existing_eval:
            eval_result = EvaluationService.update_evaluation(existing_eval, data)
            success_message = 'Cập nhật đánh giá thành công!'
        else:
            eval_result = EvaluationService.create_evaluation(
                video.video_id, 
                session['user_id'], 
                data
            )
            success_message = 'Chấm điểm thành công!'
        
        if eval_result['success']:
            grade_result = ExamService.grade_exam_result_from_evaluation(result_id, form.overall_score.data, session['user_id'])
            if grade_result['success']:
                flash(success_message, 'success')
                return redirect(url_for('instructor.exam_detail', exam_id=exam_id))
            else:
                flash(grade_result['message'], 'error')
        else:
            flash(eval_result['message'], 'error')
    
    return render_template('instructor/exam_grade.html', 
                         exam=exam, 
                         result=result, 
                         video=video,
                         reference_video_url=reference_video_url,
                         video_source=video_source,
                         form=form,
                         existing_eval=existing_eval,
                         ai_eval=ai_eval)


@instructor_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_exam(exam_id: int):
    result = ExamService.delete_exam(exam_id, session['user_id'])
    if result['success']:
        flash('Xóa bài kiểm tra thành công!', 'success')
        return redirect(url_for('instructor.exams'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('instructor.exam_detail', exam_id=exam_id))



