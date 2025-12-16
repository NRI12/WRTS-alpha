import os
import cv2
import numpy as np
import math
from ultralytics import YOLO
from scipy.signal import savgol_filter, resample
from scipy.spatial.distance import cosine, euclidean
from fastdtw import fastdtw
import gc

MODELS_DIR = os.environ.get('YOLO_MODELS_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'models'))
os.makedirs(MODELS_DIR, exist_ok=True)
if 'YOLO_MODELS_DIR' not in os.environ:
    os.environ['YOLO_MODELS_DIR'] = MODELS_DIR

class PoseScorer:
    _pose_model = None
    _model_name = "yolov8n-pose.pt"
    SMOOTH_WINDOW = 21
    SMOOTH_POLY = 3
    
    @classmethod
    def _load_pose_model(cls):
        if cls._pose_model is None:
            model_path = os.path.join(MODELS_DIR, cls._model_name)
            if os.path.exists(model_path):
                cls._pose_model = YOLO(model_path)
            else:
                cls._pose_model = YOLO(cls._model_name)
                import shutil
                try:
                    from pathlib import Path
                    ultralytics_home = Path.home() / '.ultralytics'
                    source_path = ultralytics_home / 'weights' / cls._model_name
                    if source_path.exists():
                        os.makedirs(os.path.dirname(model_path), exist_ok=True)
                        shutil.copy2(str(source_path), model_path)
                except Exception:
                    pass
        return cls._pose_model
    
    @classmethod
    def normalize_keypoints(cls, kpts):
        k = np.array(kpts).reshape(-1, 3)
        hip = (k[11, :2] + k[12, :2]) / 2
        k[:, :2] -= hip
        torso = np.linalg.norm(k[11, :2] - k[0, :2])
        if torso < 1:
            torso = 1
        k[:, :2] /= torso
        return k.flatten()

    @classmethod
    def smooth_sequence(cls, seq):
        if len(seq) < cls.SMOOTH_WINDOW:
            return seq
        out = np.zeros_like(seq)
        for i in range(seq.shape[1]):
            out[:, i] = savgol_filter(seq[:, i], cls.SMOOTH_WINDOW, cls.SMOOTH_POLY)
        return out
    
    @classmethod
    def smooth_ema(cls, data, alpha=0.25):
        out = data.copy()
        for i in range(1, len(data)):
            out[i] = alpha * out[i] + (1 - alpha) * out[i - 1]
        return out
    
    @classmethod
    def extract_template_from_video(cls, video_path: str) -> np.ndarray:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        model = cls._load_pose_model()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            res = model(frame, verbose=False)
            if len(res[0].keypoints) == 0:
                continue
            k = res[0].keypoints[0].data.cpu().numpy().flatten()
            if np.sum(k == 0) > 10:
                continue
            frames.append(cls.normalize_keypoints(k))
            del k, res
            gc.collect()
        cap.release()
        if len(frames) == 0:
            raise ValueError("No valid pose frames found in video")
        frames = np.array(frames, dtype=np.float32)
        frames = cls.smooth_sequence(frames)
        frames = cls.smooth_ema(frames)
        return frames
    
    @classmethod
    def load_teacher_template(cls, template_path: str) -> np.ndarray:
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        teacher_raw = np.load(template_path)
        if teacher_raw.shape[1] == 51:
            teacher = np.apply_along_axis(cls.normalize_keypoints, 1, teacher_raw)
        else:
            teacher = teacher_raw
        return teacher
    
    @classmethod
    def align_length(cls, teacher_kpts: np.ndarray, student_kpts: np.ndarray) -> np.ndarray:
        aligned = resample(teacher_kpts, len(student_kpts), axis=0)
        gc.collect()
        return aligned

    # ===== New scoring helpers =====
    @classmethod
    def shape_penalty(cls, student, teacher):
        d1 = np.std(student, axis=1)
        d2 = np.std(teacher, axis=1)
        diff = np.mean(np.abs(d1 - d2))
        return np.exp(-diff * 8)

    @classmethod
    def score_cosine(cls, a, b):
        base = np.mean([
            np.dot(a[i], b[i]) / (np.linalg.norm(a[i]) * np.linalg.norm(b[i]) + 1e-8)
            for i in range(len(a))
        ])
        s = base * cls.shape_penalty(a, b) * 0.9
        return max(s, 0.55)

    @classmethod
    def dtw_distance(cls, seqA, seqB):
        n, m = len(seqA), len(seqB)
        cost = np.full((n + 1, m + 1), np.inf)
        cost[0, 0] = 0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                d = np.linalg.norm(seqA[i - 1] - seqB[j - 1])
                cost[i, j] = d + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
        return cost[n, m] / (n + m)

    @classmethod
    def score_dtw(cls, student, teacher):
        d = cls.dtw_distance(student, teacher)
        return np.exp(-2.0 * d)

    @classmethod
    def score_velocity(cls, a, b):
        va = np.diff(a, axis=0)
        vb = np.diff(b, axis=0)
        c = np.corrcoef(va.flatten(), vb.flatten())[0, 1]
        if np.isnan(c):
            c = -1
        c = (c + 1) / 2
        return c ** 1.7

    @classmethod
    def score_stability(cls, student):
        v = np.diff(student, axis=0)
        a = np.diff(v, axis=0)
        j = np.diff(a, axis=0)
        mse = np.mean(v ** 2) + 3 * np.mean(a ** 2) + 15 * np.mean(j ** 2)
        return 1 / (1 + 200 * mse)

    @classmethod
    def action_similarity(cls, student, teacher):
        v1 = np.std(student, axis=0)
        v2 = np.std(teacher, axis=0)
        s = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        return (s + 1) / 2

    @classmethod
    def evaluate(cls, student, teacher):
        l = min(len(student), len(teacher))
        student = student[:l]
        teacher = teacher[:l]

        A = cls.action_similarity(student, teacher)

        if A < 0.55:
            return {
                "pose": 5,
                "speed": 5,
                "stability": 5,
                "total": 15,
                "feedback": {
                    "pose": "Không cùng bài.",
                    "speed": "Không cùng bài.",
                    "stability": "Không cùng bài.",
                },
            }

        s_pose = 0.7 * cls.score_cosine(student, teacher) + 0.3 * cls.score_dtw(student, teacher)
        s_speed = cls.score_velocity(student, teacher)
        s_stab = cls.score_stability(student)

        pose_score = s_pose * 50
        speed_score = s_speed * 30
        stab_score = s_stab * 20
        total = pose_score + speed_score + stab_score

        return {
            "pose": float(pose_score),
            "speed": float(speed_score),
            "stability": float(stab_score),
            "total": float(total),
            "feedback": {
                "pose": "Tốt" if pose_score >= 40 else "Còn lệch nhẹ" if pose_score >= 25 else "Tư thế chưa đúng",
                "speed": "Ổn" if speed_score >= 20 else "Chưa đều",
                "stability": "Ổn định" if stab_score >= 12 else "Hơi rung",
            },
        }
    
    @classmethod
    def score_video(cls, student_video_path: str, teacher_template_path: str) -> dict:
        import gc
        
        student_template = cls.extract_template_from_video(student_video_path)
        gc.collect()  # Thêm dòng này
        
        teacher_template = cls.load_teacher_template(teacher_template_path)
        result = cls.evaluate(student_template, teacher_template)
        return result
