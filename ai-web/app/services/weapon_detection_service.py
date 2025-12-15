from app import db
from app.models.training_video import TrainingVideo
from app.models.assignment import Assignment
from app.utils.storage_service import StorageService
from flask import current_app
import threading
import os
import tempfile


class WeaponDetectionService:

    @staticmethod
    def _detect_core(video_id: int, app=None):
        if app is None:
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                from app import create_app
                app = create_app()
        
        with app.app_context():
            video = None
            try:
                video = TrainingVideo.query.get(video_id)
                if not video:
                    return

                video_url = video.video_url
                temp_video_path = None
                
                if video_url.startswith('https://storage.railway.app'):
                    try:
                        temp_video_path = StorageService.download_file_to_temp(video_url)
                        video_path = temp_video_path
                    except Exception as e:
                        print(f"[WeaponDetectionService] Error downloading video from storage: {e}")
                        return
                else:
                    video_path = video_url
                    if not os.path.exists(video_path):
                        if not os.path.isabs(video_path):
                            current_file = os.path.abspath(__file__)
                            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                            rel_path = video_path.lstrip('/')
                            video_path = os.path.join(project_root, rel_path)
                    
                    if not os.path.exists(video_path):
                        print(f"[WeaponDetectionService] Video file not found: {video.video_url}")
                        return

                from app.services.ai_client_service import AIClientService
                
                import sys
                sys.stdout.flush()
                print("\n" + "="*60, flush=True)
                print("[WeaponDetectionService] Bắt đầu phát hiện vũ khí", flush=True)
                print("="*60, flush=True)
                print(f"Video ID: {video_id}", flush=True)
                print(f"Video Path: {video_path}", flush=True)
                print(f"Assignment ID: {video.assignment_id}", flush=True)
                
                print("\n[WeaponDetectionService] Đang gọi AI server để detect vũ khí...", flush=True)
                sys.stdout.flush()
                detection_result = AIClientService.detect_weapon(video_path)
                detected_weapon = detection_result.get('detected_weapon')
                confidence = detection_result.get('confidence', 0.0)
                detection_count = detection_result.get('detection_count', 0)
                total_samples = detection_result.get('total_samples', 0)
                
                print(f"\n[WeaponDetectionService] Kết quả phát hiện:", flush=True)
                print(f"  - Vũ khí phát hiện: {detected_weapon}", flush=True)
                print(f"  - Độ tin cậy: {confidence:.2%}", flush=True)
                print(f"  - Số frame phát hiện: {detection_count}/{total_samples}", flush=True)
                
                expected_weapon = None
                weapon_match = False
                
                if video.assignment_id:
                    assignment = Assignment.query.get(video.assignment_id)
                    if assignment and assignment.routine:
                        routine = assignment.routine
                        if routine.weapon:
                            expected_weapon = routine.weapon.weapon_name_vi or routine.weapon.weapon_name_en
                            
                            print(f"\n[WeaponDetectionService] Thông tin assignment:", flush=True)
                            print(f"  - Bài võ: {routine.routine_name}", flush=True)
                            print(f"  - Vũ khí yêu cầu: {expected_weapon}", flush=True)
                            
                            if detected_weapon and expected_weapon:
                                weapon_match = (detected_weapon.lower().strip() == expected_weapon.lower().strip())
                
                if detected_weapon == 'Thương' and expected_weapon == 'Giáo':
                    print(f"[WeaponDetectionService] Detected 'Thương' but expected 'Giáo' - treating as match (spear type)", flush=True)
                    detected_weapon = 'Giáo'
                    weapon_match = True
                elif detected_weapon == 'Giáo' and expected_weapon == 'Thương':
                    print(f"[WeaponDetectionService] Detected 'Giáo' but expected 'Thương' - treating as match (spear type)", flush=True)
                    detected_weapon = 'Thương'
                    weapon_match = True
                
                video.detected_weapon = detected_weapon
                
                if expected_weapon:
                    video.weapon_match_status = 'matched' if weapon_match else 'mismatched'
                else:
                    video.weapon_match_status = 'pending'
                
                db.session.commit()
                
                print(f"\n[WeaponDetectionService] Kết quả so sánh:", flush=True)
                print(f"  - Vũ khí phát hiện: {detected_weapon}", flush=True)
                print(f"  - Vũ khí yêu cầu: {expected_weapon}", flush=True)
                print(f"  - Trạng thái khớp: {'✓ KHỚP' if weapon_match else '✗ KHÔNG KHỚP' if expected_weapon else 'CHƯA XÁC ĐỊNH'}", flush=True)
                print("="*60, flush=True)
                print("[WeaponDetectionService] Hoàn thành phát hiện vũ khí\n", flush=True)
                sys.stdout.flush()

            except Exception as e:
                db.session.rollback()
                print(f"[WeaponDetectionService] Lỗi detect vũ khí cho video {video_id}: {e}")
                import traceback
                traceback.print_exc()
            finally:
                if 'temp_video_path' in locals() and temp_video_path and os.path.exists(temp_video_path):
                    try:
                        os.remove(temp_video_path)
                    except:
                        pass

    @staticmethod
    def detect_async(video_id: int):
        try:
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                from app import create_app
                app = create_app()
            
            t = threading.Thread(
                target=WeaponDetectionService._detect_core,
                args=(video_id, app),
                daemon=True,
            )
            t.start()
        except Exception as e:
            print(f"[WeaponDetectionService] Không tạo được thread, chạy sync. Lỗi: {e}")
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                from app import create_app
                app = create_app()
            WeaponDetectionService._detect_core(video_id, app)
