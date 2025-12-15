from datetime import datetime, timezone, timedelta
from markupsafe import Markup, escape
from flask import url_for

def get_vietnam_time():
    """
    Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7)
    """
    vietnam_tz = timezone(timedelta(hours=7))
    return datetime.now(vietnam_tz)

def get_vietnam_time_naive():
    """
    Lấy thời gian hiện tại theo múi giờ Việt Nam (UTC+7) nhưng trả về naive datetime
    Để tương thích với database datetime (naive)
    """
    vietnam_tz = timezone(timedelta(hours=7))
    return datetime.now(vietnam_tz).replace(tzinfo=None)

def utc_to_vietnam(utc_datetime):
    """
    Chuyển đổi UTC datetime sang múi giờ Việt Nam (UTC+7)
    """
    if utc_datetime is None:
        return None
    
    vietnam_tz = timezone(timedelta(hours=7))
    if utc_datetime.tzinfo is None:
        # Nếu datetime không có timezone info, giả sử là UTC
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    return utc_datetime.astimezone(vietnam_tz)

def vietnam_to_utc(vietnam_datetime):
    """
    Chuyển đổi múi giờ Việt Nam (UTC+7) sang UTC
    """
    if vietnam_datetime is None:
        return None
    
    vietnam_tz = timezone(timedelta(hours=7))
    if vietnam_datetime.tzinfo is None:
        # Nếu datetime không có timezone info, giả sử là Vietnam time
        vietnam_datetime = vietnam_datetime.replace(tzinfo=vietnam_tz)
    
    return vietnam_datetime.astimezone(timezone.utc)

def nl2br(value: str) -> Markup:
    if value is None:
        return Markup("")
    escaped = escape(value)
    return Markup(escaped.replace("\n", "<br>\n"))

def get_video_url(video_url):
    """Helper function để lấy video URL, tự động dùng presigned URL nếu là Railway storage URL"""
    if not video_url:
        return ""
    
    if video_url.startswith('https://storage.railway.app'):
        try:
            from app.utils.storage_service import StorageService
            from flask import current_app
            try:
                presigned_url = StorageService.get_presigned_url(video_url, expiration=3600)
                return presigned_url
            except:
                try:
                    s3_client, bucket_name = StorageService._get_s3_client()
                    if bucket_name in video_url:
                        file_path = video_url.split(f"{bucket_name}/", 1)[1]
                        return url_for('shared.serve_storage_file', file_path=file_path, _external=True)
                except:
                    pass
                return video_url
        except:
            return video_url
    elif video_url.startswith('/static/'):
        return video_url
    else:
        return video_url
