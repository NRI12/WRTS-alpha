# test.py
import requests
import os
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "https://ctv55345--ai-server"  # ← ĐÃ SỬA
VIDEO_DIR = r"C:\Users\nguye\Pictures\ĐATN_H.anh_Final_10-12\Score_Compare"
TIMEOUT = 1800  # 30 phút

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_file_size_mb(file_path):
    """Lấy kích thước file (MB)"""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

def print_header(title):
    """In header đẹp"""
    print("\n" + "="*60)
    print(title)
    print("="*60)

# ============================================================
# TEST FUNCTIONS
# ============================================================
def test_health():
    """Test health check"""
    print_header("Testing Health Check")
    url = f"{BASE_URL}--health.modal.run"
    print(f"🔍 URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_weapon_detection(video_path):
    """Test weapon detection"""
    url = f"{BASE_URL}--weapon-detect.modal.run"
    file_name = os.path.basename(video_path)
    file_size = get_file_size_mb(video_path)
    
    print(f"\n🔍 Testing Weapon Detection: {file_name} ({file_size:.2f} MB)")
    print(f"   Uploading...", end=" ", flush=True)
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (file_name, f, 'video/mp4')}
            data = {}  # Empty data dict
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=TIMEOUT
            )
        
        print("Done")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Response: {response.json()}")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n   ❌ Timeout: Request took longer than {TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n   ❌ Connection Error: {str(e)[:100]}")
        print(f"   💡 Tip: Check if endpoint is correct or server is busy")
        return False
    except Exception as e:
        print(f"\n   ❌ Unexpected Error: {type(e).__name__}: {str(e)[:150]}")
        return False

def test_extract_template(video_path):
    """Test extract template"""
    url = f"{BASE_URL}--pose-extract-template.modal.run"
    file_name = os.path.basename(video_path)
    file_size = get_file_size_mb(video_path)
    
    print(f"\n🔍 Testing Extract Template: {file_name} ({file_size:.2f} MB)")
    print(f"   Uploading...", end=" ", flush=True)
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (file_name, f, 'video/mp4')}
            data = {}
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=TIMEOUT
            )
        
        print("Done")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Template extracted successfully")
            if 'template' in result:
                print(f"   Template shape: {len(result['template'])} frames")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n   ❌ Timeout: Request took longer than {TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n   ❌ Connection Error: {str(e)[:100]}")
        return False
    except Exception as e:
        print(f"\n   ❌ Unexpected Error: {type(e).__name__}: {str(e)[:150]}")
        return False

def test_pose_score(video_path, template_path):
    """Test pose scoring"""
    url = f"{BASE_URL}--pose-score.modal.run"
    video_name = os.path.basename(video_path)
    template_name = os.path.basename(template_path)
    video_size = get_file_size_mb(video_path)
    
    print(f"\n🔍 Testing Pose Score: {video_name} ({video_size:.2f} MB) vs {template_name}")
    print(f"   Uploading...", end=" ", flush=True)
    
    try:
        with open(video_path, 'rb') as vf, open(template_path, 'rb') as tf:
            files = {
                'video': (video_name, vf, 'video/mp4'),
                'template': (template_name, tf, 'application/octet-stream')
            }
            data = {}
            
            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=TIMEOUT
            )
        
        print("Done")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Score: {result.get('score', 'N/A')}")
            print(f"   Details: {result}")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n   ❌ Timeout: Request took longer than {TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n   ❌ Connection Error: {str(e)[:100]}")
        return False
    except Exception as e:
        print(f"\n   ❌ Unexpected Error: {type(e).__name__}: {str(e)[:150]}")
        return False

# ============================================================
# MAIN
# ============================================================
def main():
    print("="*60)
    print("AI Server API Test")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Video Directory: {VIDEO_DIR}")
    print(f"Timeout: {TIMEOUT} seconds")
    print("="*60)
    
    # Test health first
    if not test_health():
        print("\n⚠️  Health check failed! Stopping tests.")
        return
    
    # Get video files
    video_files = [f for f in os.listdir(VIDEO_DIR) 
                   if f.endswith(('.mp4', '.avi', '.mov'))]
    template_files = [f for f in os.listdir(VIDEO_DIR) 
                      if f.endswith('.npy')]
    
    print(f"\n📹 Found {len(video_files)} video files")
    print(f"📦 Found {len(template_files)} template files")
    
    # Test Weapon Detection
    print_header("Testing Weapon Detection")
    for video_file in video_files[:3]:  # Test first 3 videos
        video_path = os.path.join(VIDEO_DIR, video_file)
        test_weapon_detection(video_path)
    
    # Test Extract Template
    print_header("Testing Extract Template")
    if video_files:
        # Test with teacher video
        teacher_videos = [v for v in video_files if 'teacher' in v.lower()]
        test_video = teacher_videos[0] if teacher_videos else video_files[0]
        video_path = os.path.join(VIDEO_DIR, test_video)
        test_extract_template(video_path)
    
    # Test Pose Score
    print_header("Testing Pose Score")
    if video_files and template_files:
        video_path = os.path.join(VIDEO_DIR, video_files[0])
        template_path = os.path.join(VIDEO_DIR, template_files[0])
        test_pose_score(video_path, template_path)
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60)

if __name__ == "__main__":
    main()