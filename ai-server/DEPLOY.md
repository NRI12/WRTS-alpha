# Deploy to Modal.ai

## Setup

1. Install dependencies:
```bash
pip install modal python-dotenv
```

2. Authenticate:
```bash
modal token new
```

3. Cấu hình môi trường:
```bash
# Copy file .env.example thành .env
cp .env.example .env

# Chỉnh sửa file .env và điền các tham số quan trọng:
# - GOOGLE_DRIVE_FILE_ID: File ID của model trên Google Drive
# - Các tham số khác có thể giữ nguyên hoặc tùy chỉnh
```

## Cấu trúc Config

- `config.py`: Chứa tất cả các cấu hình (Python packages, system packages, paths, etc.)
- `.env`: Chứa các tham số quan trọng và sensitive (Google Drive File ID, timeouts, etc.)
- `.env.example`: Template cho file .env

## Deploy

```bash
modal deploy deploy.py
```

## Endpoints

After deployment, you'll get URLs like:
- `https://<workspace>--health.modal.run` - Health check
- `https://<workspace>--weapon-detect.modal.run` - Weapon detection
- `https://<workspace>--pose-extract-template.modal.run` - Extract template
- `https://<workspace>--pose-score.modal.run` - Score pose

## Testing

### 1. Test với Python Script

```bash
# Cài đặt requests (nếu chưa có)
pip install requests

# Test tất cả endpoints
python test_endpoints.py https://your-workspace--health.modal.run

# Test với video file
python test_endpoints.py https://your-workspace--health.modal.run path/to/video.mp4
```

### 2. Test với cURL

```bash
# Test Health Check
curl https://your-workspace--health.modal.run

# Test Weapon Detection (với video file)
curl -X POST https://your-workspace--weapon-detect.modal.run \
  -F "video=@path/to/video.mp4"

# Test Pose Extract Template
curl -X POST https://your-workspace--pose-extract-template.modal.run \
  -F "video=@path/to/video.mp4"

# Test Pose Score
curl -X POST https://your-workspace--pose-score.modal.run \
  -F "student_video=@student.mp4" \
  -F "teacher_template=@template.npy"
```

### 3. Test với Postman/Thunder Client

1. **Health Check**:
   - Method: `GET`
   - URL: `https://your-workspace--health.modal.run`

2. **Weapon Detection**:
   - Method: `POST`
   - URL: `https://your-workspace--weapon-detect.modal.run`
   - Body: `form-data`
   - Key: `video` (type: File)
   - Value: Chọn video file

3. **Pose Extract Template**:
   - Method: `POST`
   - URL: `https://your-workspace--pose-extract-template.modal.run`
   - Body: `form-data`
   - Key: `video` (type: File)
   - Value: Chọn video file

4. **Pose Score**:
   - Method: `POST`
   - URL: `https://your-workspace--pose-score.modal.run`
   - Body: `form-data`
   - Key: `student_video` (type: File)
   - Key: `teacher_template` (type: File)

### 4. Test Local (trước khi deploy)

```bash
# Chạy local với Modal
modal serve deploy.py

# Sau đó test với localhost URLs được cung cấp
```

## Update Main Server

Update `AI_SERVER_URL` in main server to point to Modal endpoints.

## Cấu hình

Tất cả các tham số có thể được tùy chỉnh trong:
- `config.py`: Cấu hình code (packages, paths)
- `.env`: Cấu hình runtime (file IDs, timeouts, concurrent inputs)

