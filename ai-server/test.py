import os
import requests
import glob
from pathlib import Path
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "").strip()
if AI_SERVER_URL:
    if "--health" in AI_SERVER_URL:
        BASE_URL = AI_SERVER_URL.replace("--health.modal.run", "").replace("--health", "")
    elif ".modal.run" in AI_SERVER_URL:
        BASE_URL = AI_SERVER_URL.split(".modal.run")[0]
    elif "localhost" in AI_SERVER_URL or "127.0.0.1" in AI_SERVER_URL:
        BASE_URL = AI_SERVER_URL.rstrip("/")
    else:
        BASE_URL = AI_SERVER_URL
else:
    BASE_URL = "https://ctv55345"

VIDEO_DIR = r"C:\Users\nguye\Pictures\ĐATN_H.anh_Final_10-12\Score_Compare"

def create_session():
    """Create requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_endpoint_url(endpoint):
    """Get full URL for endpoint"""
    if "localhost" in BASE_URL or "127.0.0.1" in BASE_URL:
        return f"{BASE_URL}/{endpoint}"
    else:
        return f"{BASE_URL}--{endpoint}.modal.run"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing Health Check...")
    try:
        url = get_endpoint_url("health")
        print(f"   URL: {url}")
        session = create_session()
        response = session.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   💡 Tip: Set AI_SERVER_URL environment variable")
        print(f"   Example: set AI_SERVER_URL=https://your-workspace--health.modal.run")
        return False

def test_weapon_detect(video_path):
    """Test weapon detection"""
    video_name = os.path.basename(video_path)
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n🔍 Testing Weapon Detection: {video_name} ({file_size:.2f} MB)")
    try:
        url = get_endpoint_url("weapon-detect")
        session = create_session()
        
        print("   Uploading...", end="", flush=True)
        with open(video_path, 'rb') as f:
            files = {'video': (video_name, f, 'video/mp4')}
            response = session.post(url, files=files, timeout=600)
        print(" Done")
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if 'error' in result:
                    print(f"   ❌ Error: {result['error']}")
                    return False
                else:
                    print(f"   ✅ Detected: {result.get('has_weapon', 'N/A')}")
                    print(f"   Confidence: {result.get('confidence', 'N/A')}")
                    return True
            except ValueError:
                print(f"   ❌ Invalid JSON response: {response.text[:200]}")
                return False
        else:
            try:
                error = response.json()
                print(f"   ❌ Error: {error.get('error', response.text[:200])}")
            except:
                print(f"   ❌ Error: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout: Request took longer than 10 minutes")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {str(e)[:100]}")
        print(f"   💡 Tip: File might be too large or server is busy")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return False

def test_extract_template(video_path):
    """Test extract template"""
    video_name = os.path.basename(video_path)
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n🔍 Testing Extract Template: {video_name} ({file_size:.2f} MB)")
    try:
        url = get_endpoint_url("pose-extract-template")
        session = create_session()
        
        print("   Uploading...", end="", flush=True)
        with open(video_path, 'rb') as f:
            files = {'video': (video_name, f, 'video/mp4')}
            response = session.post(url, files=files, timeout=600)
        print(" Done")
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if 'error' in result:
                    print(f"   ❌ Error: {result['error']}")
                    return False
                else:
                    template_len = len(result.get('template_base64', ''))
                    if template_len > 0:
                        print(f"   ✅ Template extracted: {template_len} chars")
                        return True
                    else:
                        print(f"   ⚠️  Warning: Template is empty")
                        return False
            except ValueError:
                print(f"   ❌ Invalid JSON response: {response.text[:200]}")
                return False
        else:
            try:
                error = response.json()
                print(f"   ❌ Error: {error.get('error', error.get('detail', response.text[:200]))}")
            except:
                print(f"   ❌ Error: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout: Request took longer than 10 minutes")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {str(e)[:100]}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return False

def test_pose_score(student_video, teacher_template):
    """Test pose scoring"""
    student_name = os.path.basename(student_video)
    template_name = os.path.basename(teacher_template)
    file_size = os.path.getsize(student_video) / (1024 * 1024)
    print(f"\n🔍 Testing Pose Score: {student_name} ({file_size:.2f} MB) vs {template_name}")
    try:
        url = get_endpoint_url("pose-score")
        session = create_session()
        
        print("   Uploading...", end="", flush=True)
        with open(student_video, 'rb') as sv, open(teacher_template, 'rb') as tt:
            files = {
                'student_video': (student_name, sv, 'video/mp4'),
                'teacher_template': (template_name, tt, 'application/octet-stream')
            }
            response = session.post(url, files=files, timeout=600)
        print(" Done")
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if 'error' in result:
                    print(f"   ❌ Error: {result['error']}")
                    return False
                else:
                    score = result.get('score', 'N/A')
                    print(f"   ✅ Score: {score}")
                    return True
            except ValueError:
                print(f"   ❌ Invalid JSON response: {response.text[:200]}")
                return False
        else:
            try:
                error = response.json()
                print(f"   ❌ Error: {error.get('error', error.get('detail', response.text[:200]))}")
            except:
                print(f"   ❌ Error: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout: Request took longer than 10 minutes")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {str(e)[:100]}")
        print(f"   💡 Tip: File might be too large or server is busy")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")
        return False

def main():
    import sys
    
    print("=" * 60)
    print("AI Server API Test")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Video Directory: {VIDEO_DIR}")
    print("=" * 60)
    
    if not os.path.exists(VIDEO_DIR):
        print(f"❌ Video directory not found: {VIDEO_DIR}")
        return
    
    if BASE_URL == "https://your-workspace":
        print("⚠️  Warning: Using default BASE_URL. Please set AI_SERVER_URL or edit BASE_URL in test.py")
        print("   Example: set AI_SERVER_URL=https://your-workspace--health.modal.run")
        print()
    
    test_health()
    
    video_files = glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))
    template_files = glob.glob(os.path.join(VIDEO_DIR, "*.npy"))
    
    print(f"\n📹 Found {len(video_files)} video files")
    print(f"📦 Found {len(template_files)} template files")
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "weapon":
            print("\n" + "=" * 60)
            print("Testing Weapon Detection Only")
            print("=" * 60)
            for video in video_files[:3]:
                test_weapon_detect(video)
        elif test_type == "template":
            print("\n" + "=" * 60)
            print("Testing Extract Template Only")
            print("=" * 60)
            teacher_video = next((v for v in video_files if 'teacher' in v.lower() or 'Teacher' in v), video_files[0])
            test_extract_template(teacher_video)
        elif test_type == "score":
            print("\n" + "=" * 60)
            print("Testing Pose Score Only")
            print("=" * 60)
            student_videos = [v for v in video_files if 'student' in v.lower() or 'Student' in v]
            if template_files:
                teacher_template = template_files[0]
                for student_video in student_videos[:3]:
                    test_pose_score(student_video, teacher_template)
            else:
                print("❌ No template files found")
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("Usage: python test.py [weapon|template|score]")
            return
    else:
        if video_files:
            print("\n" + "=" * 60)
            print("Testing Weapon Detection")
            print("=" * 60)
            for video in video_files[:3]:
                test_weapon_detect(video)
        
        if video_files:
            print("\n" + "=" * 60)
            print("Testing Extract Template")
            print("=" * 60)
            teacher_video = next((v for v in video_files if 'teacher' in v.lower() or 'Teacher' in v), video_files[0])
            test_extract_template(teacher_video)
        
        if video_files and template_files:
            print("\n" + "=" * 60)
            print("Testing Pose Score")
            print("=" * 60)
            student_videos = [v for v in video_files if 'student' in v.lower() or 'Student' in v]
            teacher_template = template_files[0]
            
            for student_video in student_videos[:3]:
                test_pose_score(student_video, teacher_template)
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)
    print("\n💡 Tip: Test individual endpoints with:")
    print("   python test.py weapon   - Test weapon detection only")
    print("   python test.py template - Test extract template only")
    print("   python test.py score    - Test pose score only")

if __name__ == "__main__":
    main()

