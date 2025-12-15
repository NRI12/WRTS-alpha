import os
import gdown

MODELS_DIR = os.environ.get('YOLO_MODELS_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'models'))
os.makedirs(MODELS_DIR, exist_ok=True)

WEAPON_MODEL_PATH = os.path.join(MODELS_DIR, 'weapon_detection', 'best.pt')

def ensure_weapon_model():
    if os.path.exists(WEAPON_MODEL_PATH):
        return WEAPON_MODEL_PATH
    file_id = "11twpIDRYgAelMkat3DwXOUI3k1BBgYl8"
    url = f"https://drive.google.com/uc?id={file_id}"
    os.makedirs(os.path.dirname(WEAPON_MODEL_PATH), exist_ok=True)
    gdown.download(url, WEAPON_MODEL_PATH, quiet=False)
    if not os.path.exists(WEAPON_MODEL_PATH):
        raise FileNotFoundError(f"Failed to download weapon model to {WEAPON_MODEL_PATH}")
    return WEAPON_MODEL_PATH

