from datetime import datetime, timezone, timedelta
from markupsafe import Markup, escape
from flask import url_for
from app.utils.storage_service import StorageService

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
    if not video_url:
        return ""

    if video_url.startswith('https://storage.railway.app'):
        try:
            return StorageService.get_presigned_url(video_url)
        except Exception:
            return video_url

    if video_url.startswith('/static/'):
        return video_url

    return video_url
