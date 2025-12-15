import os
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import pathlib
from app.utils.model_loader import ensure_weapon_model

class WeaponDetector:
    _model = None
    _model_path = None
    WEAPON_MAPPING = {
        'sword': 'Kiếm',
        'spear': 'Thương',
        'stick': 'Côn',
    }
    
    @classmethod
    def _get_model_path(cls):
        if cls._model_path is None:
            cls._model_path = ensure_weapon_model()
        return cls._model_path
    
    @classmethod
    def _load_model(cls):
        if cls._model is None:
            model_path = cls._get_model_path()
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            cls._model = YOLO(model_path)
        return cls._model
    
    @classmethod
    def detect_from_video(cls, video_path: str) -> dict:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        model = cls._load_model()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return {'detected_weapon': None, 'confidence': 0.0, 'detection_count': 0, 'total_samples': 1}
        results = model(frame, verbose=False)
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = model.names[cls_id].lower()
                    weapon_name = cls._map_weapon_name(cls_name)
                    if weapon_name:
                        detections.append({
                            'weapon': weapon_name,
                            'confidence': conf
                        })
        if not detections:
            return {'detected_weapon': None, 'confidence': 0.0, 'detection_count': 0, 'total_samples': 1}
        best = max(detections, key=lambda x: x['confidence'])
        return {
            'detected_weapon': best['weapon'],
            'confidence': best['confidence'],
            'detection_count': 1,
            'total_samples': 1
        }
    
    @classmethod
    def detect_from_image(cls, image_path: str) -> dict:
        if image_path.lower().endswith(".jfif"):
            jpg_path = str(pathlib.Path(image_path).with_suffix(".jpg"))
            img = Image.open(image_path)
            img.save(jpg_path, "JPEG")
            image_path = jpg_path
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        model = cls._load_model()
        results = model(image_path, verbose=False)
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = model.names[cls_id].lower()
                    weapon_name = cls._map_weapon_name(cls_name)
                    if weapon_name:
                        detections.append({
                            'weapon': weapon_name,
                            'confidence': conf
                        })
        if not detections:
            return {'detected_weapon': None, 'confidence': 0.0, 'detection_count': 0}
        best = max(detections, key=lambda x: x['confidence'])
        return {
            'detected_weapon': best['weapon'],
            'confidence': best['confidence'],
            'detection_count': len(detections)
        }
    
    @classmethod
    def _map_weapon_name(cls, detected_name: str) -> str:
        detected_name = detected_name.lower().strip()
        return cls.WEAPON_MAPPING.get(detected_name)
