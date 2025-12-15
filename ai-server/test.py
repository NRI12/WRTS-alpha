# test.py - Version có debug
import requests
import os
import time

WORKSPACE = "ctv55345"
APP_NAME = "ai-server"
VIDEO_DIR = r"C:\Users\nguye\Pictures\ĐATN_H.anh_Final_10-12\Score_Compare"

def get_url(endpoint):
    # Endpoint mới qua FastAPI
    return f"https://{WORKSPACE}--{APP_NAME}-fastapi-app.modal.run/{endpoint}"

def upload_file(url, files, timeout=300):
    """Upload file với retry và debug"""
    for i in range(2):
        try:
            print(f"   Upload (lần {i+1})...", end=" ")
            res = requests.post(url, files=files, timeout=timeout)
            print(f"Status: {res.status_code}")
            
            # Debug response
            if res.status_code != 200:
                print(f"   ❌ Error response: {res.text[:300]}")
            
            return res
        except Exception as e:
            print(f"❌ {type(e).__name__}: {str(e)[:100]}")
            if i == 0:
                time.sleep(3)
    return None

def test_health():
    print("\n1️⃣ TEST HEALTH")
    # Health endpoint vẫn là web_endpoint riêng trên Modal, không đi qua FastAPI app
    url = f"https://{WORKSPACE}--health.modal.run"
    res = requests.get(url, timeout=10)
    print(f"   {res.json()}")
    return res.status_code == 200

def test_weapon(video_file):
    print(f"\n2️⃣ TEST WEAPON - {video_file}")
    url = get_url("weapon/detect")
    path = os.path.join(VIDEO_DIR, video_file)
    
    with open(path, 'rb') as f:
        # Thử cả 2 cách
        print("   Cách 1: field='video'")
        files = {'video': (video_file, f, 'video/mp4')}
        res = upload_file(url, files)
        
        if res and res.status_code == 200:
            print(f"   ✅ Result: {res.json()}")
            return True
    
    # Thử cách 2 nếu cách 1 fail
    with open(path, 'rb') as f:
        print("   Cách 2: field='file'")
        files = {'file': (video_file, f, 'video/mp4')}
        res = upload_file(url, files)
        
        if res and res.status_code == 200:
            print(f"   ✅ Result: {res.json()}")
            return True
    
    return False

def test_extract(video_file):
    print(f"\n3️⃣ TEST EXTRACT - {video_file}")
    url = get_url("pose/extract-template")
    path = os.path.join(VIDEO_DIR, video_file)
    
    with open(path, 'rb') as f:
        files = {'video': (video_file, f, 'video/mp4')}
        res = upload_file(url, files)
    
    if res and res.status_code == 200:
        print(f"   ✅ Success")
        return True
    return False

def test_score(video_file, template_file):
    print(f"\n4️⃣ TEST SCORE")
    print(f"   Video: {video_file}")
    print(f"   Template: {template_file}")
    
    url = get_url("pose/score")
    video_path = os.path.join(VIDEO_DIR, video_file)
    template_path = os.path.join(VIDEO_DIR, template_file)
    
    with open(video_path, 'rb') as v, open(template_path, 'rb') as t:
        files = {
            'student_video': (video_file, v, 'video/mp4'),
            'teacher_template': (template_file, t, 'application/octet-stream')
        }
        res = upload_file(url, files, timeout=600)
    
    if res and res.status_code == 200:
        print(f"   ✅ Score: {res.json()}")
        return True
    return False

def main():
    print("="*60)
    print("AI SERVER DEBUG TEST")
    print("="*60)
    
    if not test_health():
        print("\n❌ Health check failed!")
        return
    
    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
    templates = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.npy')]
    
    if not videos:
        print("\n❌ Không tìm thấy video!")
        return
    
    videos.sort(key=lambda f: os.path.getsize(os.path.join(VIDEO_DIR, f)))
    small_video = videos[0]
    
    print(f"\n📹 File test: {small_video}")
    
    # Test từng endpoint
    test_weapon(small_video)
    
    teacher_videos = [v for v in videos if 'teacher' in v.lower()]
    test_video = teacher_videos[0] if teacher_videos else small_video
    test_extract(test_video)
    
    if templates:
        test_score(small_video, templates[0])
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()