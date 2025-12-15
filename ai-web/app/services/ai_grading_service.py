from app import db
from app.models.training_video import TrainingVideo
from app.models.manual_evaluation import ManualEvaluation
from app.models.assignment import Assignment
from app.services.ai_client_service import AIClientService
from app.utils.storage_service import StorageService
from flask import current_app
import threading
import os
import sys
import base64
import tempfile
import numpy as np


class AIGradingService:
    
    @staticmethod
    def _get_teacher_template_path(assignment_id: int) -> str:
        assignment = Assignment.query.get(assignment_id)
        if not assignment or not assignment.instructor_video_url:
            raise ValueError(f"No instructor video found for assignment {assignment_id}")
        
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        templates_dir = os.path.join(project_root, 'static', 'uploads', 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        template_filename = f"teacher_template_assignment_{assignment_id}.npy"
        template_path = os.path.join(templates_dir, template_filename)
        
        if not os.path.exists(template_path):
            print(f"[AIGradingService] Teacher template not found, generating from instructor video...", flush=True)
            
            instructor_video_url = assignment.instructor_video_url
            temp_instructor_path = None
            
            if instructor_video_url.startswith('https://storage.railway.app'):
                try:
                    temp_instructor_path = StorageService.download_file_to_temp(instructor_video_url)
                    instructor_video_path = temp_instructor_path
                except Exception as e:
                    print(f"[AIGradingService] ERROR downloading instructor video from storage: {e}", flush=True)
                    return None
            else:
                instructor_video_path = instructor_video_url
                if not os.path.isabs(instructor_video_path):
                    rel_path = instructor_video_path.lstrip('/').replace('/', os.sep).replace('\\', os.sep)
                    instructor_video_path = os.path.join(project_root, rel_path)
                    instructor_video_path = os.path.normpath(instructor_video_path)
                
                print(f"[AIGradingService] Instructor video path (normalized): {instructor_video_path}", flush=True)
                
                if not os.path.exists(instructor_video_path):
                    print(f"[AIGradingService] ERROR: Instructor video not found: {assignment.instructor_video_url} (tried: {instructor_video_path})", flush=True)
                    return None
            
            print(f"[AIGradingService] Extracting template from instructor video: {instructor_video_path}", flush=True)
            sys.stdout.flush()
            
            try:
                print(f"[AIGradingService] Calling AI server to extract template...", flush=True)
                sys.stdout.flush()
                template_result = AIClientService.extract_template(instructor_video_path)
                
                template_base64 = template_result['template_base64']
                template_bytes = base64.b64decode(template_base64)
                
                import io
                template_buffer = io.BytesIO(template_bytes)
                teacher_template = np.load(template_buffer)
                
                np.save(template_path, teacher_template)
                print(f"[AIGradingService] Teacher template saved to: {template_path}", flush=True)
                print(f"[AIGradingService] Template shape: {teacher_template.shape}", flush=True)
                sys.stdout.flush()
                
            except Exception as e:
                print(f"[AIGradingService] ERROR generating template: {e}", flush=True)
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
                return None
            finally:
                if temp_instructor_path and os.path.exists(temp_instructor_path):
                    try:
                        os.remove(temp_instructor_path)
                    except:
                        pass
        
        return template_path if os.path.exists(template_path) else None
    
    @staticmethod
    def _grade_core(video_id: int, app=None):
        if app is None:
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                from app import create_app
                app = create_app()
        
        with app.app_context():
            video = None
            try:
                import sys
                print(f"\n[AIGradingService] _grade_core started for video_id: {video_id}", flush=True)
                sys.stdout.flush()
                
                video = TrainingVideo.query.get(video_id)
                if not video:
                    print(f"[AIGradingService] Video {video_id} not found", flush=True)
                    return
                
                print(f"[AIGradingService] Video found: {video_id}, assignment_id: {video.assignment_id}", flush=True)
                
                if not video.assignment_id:
                    print(f"[AIGradingService] Video {video_id} has no assignment_id, skipping", flush=True)
                    return
                
                assignment = Assignment.query.get(video.assignment_id)
                if not assignment:
                    print(f"[AIGradingService] Assignment {video.assignment_id} not found", flush=True)
                    return
                
                print(f"[AIGradingService] Assignment found: {video.assignment_id}, grading_method: {assignment.grading_method}", flush=True)
                
                print(f"[AIGradingService] Getting teacher template path...", flush=True)
                teacher_template_path = AIGradingService._get_teacher_template_path(video.assignment_id)
                if not teacher_template_path:
                    print(f"[AIGradingService] ERROR: No teacher template found for assignment {video.assignment_id}", flush=True)
                    print(f"[AIGradingService] Instructor video URL: {assignment.instructor_video_url if assignment else 'N/A'}", flush=True)
                    sys.stdout.flush()
                    return
                
                print(f"[AIGradingService] Teacher template path: {teacher_template_path}", flush=True)
                sys.stdout.flush()
                
                student_video_url = video.video_url
                temp_student_path = None
                
                if student_video_url.startswith('https://storage.railway.app'):
                    try:
                        temp_student_path = StorageService.download_file_to_temp(student_video_url)
                        student_video_path = temp_student_path
                    except Exception as e:
                        print(f"[AIGradingService] ERROR downloading student video from storage: {e}", flush=True)
                        sys.stdout.flush()
                        return
                else:
                    student_video_path = student_video_url
                    if not os.path.exists(student_video_path):
                        if not os.path.isabs(student_video_path):
                            current_file = os.path.abspath(__file__)
                            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                            rel_path = student_video_path.lstrip('/').replace('/', os.sep).replace('\\', os.sep)
                            student_video_path = os.path.join(project_root, rel_path)
                            student_video_path = os.path.normpath(student_video_path)
                    
                    print(f"[AIGradingService] Student video path (normalized): {student_video_path}", flush=True)
                    
                    if not os.path.exists(student_video_path):
                        print(f"[AIGradingService] Student video not found: {video.video_url} (tried: {student_video_path})", flush=True)
                        sys.stdout.flush()
                        return
                
                import sys
                sys.stdout.flush()
                print("\n" + "="*60, flush=True)
                print("[AIGradingService] Bắt đầu chấm điểm AI", flush=True)
                print("="*60, flush=True)
                print(f"Video ID: {video_id}", flush=True)
                print(f"Student Video: {student_video_path}", flush=True)
                print(f"Teacher Template: {teacher_template_path}", flush=True)
                print(f"Assignment ID: {video.assignment_id}", flush=True)
                if assignment and assignment.routine:
                    print(f"Bài võ: {assignment.routine.routine_name}", flush=True)
                
                print("\n[AIGradingService] Đang gọi AI server để chấm điểm...", flush=True)
                sys.stdout.flush()
                result = AIClientService.score_pose(student_video_path, teacher_template_path)
                
                print(f"\n[AIGradingService] Kết quả chấm điểm:", flush=True)
                print(f"  - Điểm tổng: {result['total_score']}/100", flush=True)
                print(f"  - Điểm độ chính xác (Kỹ thuật): {result['accuracy_score']}/50", flush=True)
                print(f"  - Điểm tốc độ (Tinh thần): {result['speed_score']}/30", flush=True)
                print(f"  - Điểm ổn định (Tư thế): {result['stability_score']}/20", flush=True)
                print(f"\n[AIGradingService] Metrics chi tiết:", flush=True)
                print(f"  - Cosine Similarity: {result['metrics']['cosine_similarity']:.4f}", flush=True)
                print(f"  - DTW Distance: {result['metrics']['dtw_distance']:.2f}", flush=True)
                print(f"  - Jitter MSE: {result['metrics']['jitter_mse']:.6f}", flush=True)
                print(f"\n[AIGradingService] Feedback:", flush=True)
                for i, fb in enumerate(result['feedback'], 1):
                    print(f"  {i}. {fb}", flush=True)
                
                existing = ManualEvaluation.query.filter_by(
                    video_id=video_id,
                    evaluation_method='ai'
                ).first()
                
                if existing:
                    print(f"\n[AIGradingService] Cập nhật đánh giá AI hiện có...", flush=True)
                    existing.overall_score = result['total_score']
                    existing.technique_score = result['accuracy_score']
                    existing.posture_score = result['stability_score']
                    existing.spirit_score = result['speed_score']
                    comments = "\n".join(result['feedback'])
                    existing.comments = comments
                    from app.utils.helpers import get_vietnam_time
                    existing.evaluated_at = get_vietnam_time()
                else:
                    print(f"\n[AIGradingService] Tạo đánh giá AI mới...", flush=True)
                    from app.utils.helpers import get_vietnam_time
                    evaluation = ManualEvaluation(
                        video_id=video_id,
                        instructor_id=assignment.assigned_by,
                        overall_score=result['total_score'],
                        technique_score=result['accuracy_score'],
                        posture_score=result['stability_score'],
                        spirit_score=result['speed_score'],
                        comments="\n".join(result['feedback']),
                        evaluation_method='ai',
                        evaluated_at=get_vietnam_time()
                    )
                    db.session.add(evaluation)
                
                video.processing_status = 'completed'
                from app.utils.helpers import get_vietnam_time
                video.processed_at = get_vietnam_time()
                
                db.session.commit()
                
                print(f"\n[AIGradingService] Đã lưu kết quả vào database", flush=True)
                print("="*60, flush=True)
                print(f"[AIGradingService] Hoàn thành chấm điểm AI - Video {video_id}: {result['total_score']}/100\n", flush=True)
                sys.stdout.flush()
                
            except Exception as e:
                db.session.rollback()
                import sys
                print(f"\n[AIGradingService] ERROR grading video {video_id}: {e}", flush=True)
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
            finally:
                if 'temp_student_path' in locals() and temp_student_path and os.path.exists(temp_student_path):
                    try:
                        os.remove(temp_student_path)
                    except:
                        pass
    
    @staticmethod
    def grade_async(video_id: int):
        import sys
        print(f"\n[AIGradingService] grade_async called for video_id: {video_id}", flush=True)
        try:
            try:
                app = current_app._get_current_object()
                print(f"[AIGradingService] Got app from current_app", flush=True)
            except RuntimeError:
                from app import create_app
                app = create_app()
                print(f"[AIGradingService] Created new app instance", flush=True)
            
            print(f"[AIGradingService] Starting background thread for grading...", flush=True)
            t = threading.Thread(
                target=AIGradingService._grade_core,
                args=(video_id, app),
                daemon=True
            )
            t.start()
            print(f"[AIGradingService] Thread started successfully", flush=True)
            sys.stdout.flush()
        except Exception as e:
            print(f"[AIGradingService] Failed to start grading thread: {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                from app import create_app
                app = create_app()
            AIGradingService._grade_core(video_id, app)
