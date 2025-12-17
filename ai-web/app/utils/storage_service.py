import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
import tempfile
from werkzeug.utils import secure_filename
import uuid


class StorageService:
    
    @staticmethod
    def _get_s3_client():
        try:
            from flask import current_app
            endpoint_url = current_app.config.get('RAILWAY_STORAGE_ENDPOINT', 'https://storage.railway.app')
            access_key = current_app.config.get('RAILWAY_STORAGE_ACCESS_KEY')
            secret_key = current_app.config.get('RAILWAY_STORAGE_SECRET_KEY')
            bucket_name = current_app.config.get('RAILWAY_STORAGE_BUCKET')
        except RuntimeError:
            endpoint_url = os.getenv('RAILWAY_STORAGE_ENDPOINT', 'https://storage.railway.app')
            access_key = os.getenv('RAILWAY_STORAGE_ACCESS_KEY')
            secret_key = os.getenv('RAILWAY_STORAGE_SECRET_KEY')
            bucket_name = os.getenv('RAILWAY_STORAGE_BUCKET')
        
        if not all([access_key, secret_key, bucket_name]):
            raise ValueError("Railway storage credentials not configured")
        
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='auto'
        )
        
        return s3_client, bucket_name, endpoint_url
    
    @staticmethod
    def upload_file(file, folder='uploads', filename=None):
        try:
            s3_client, bucket_name, endpoint_url = StorageService._get_s3_client()
            
            if not filename:
                original_filename = secure_filename(file.filename) if file.filename else 'file'
                ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp4'
                filename = f"{uuid.uuid4().hex}.{ext}"
            
            s3_key = f"{folder}/{filename}"
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                s3_client.upload_file(
                    temp_file_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': file.content_type or 'application/octet-stream',
                        'ACL': 'public-read'
                    }
                )
                
                public_url = f"{endpoint_url.rstrip('/')}/{bucket_name}/{s3_key}"
                
                return public_url
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    
        except Exception as e:
            raise Exception(f"Error uploading file to storage: {str(e)}")
    
    @staticmethod
    def upload_file_from_path(file_path, folder='uploads', filename=None):
        try:
            s3_client, bucket_name, endpoint_url = StorageService._get_s3_client()
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not filename:
                original_filename = os.path.basename(file_path)
                ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
                filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
            
            s3_key = f"{folder}/{filename}"
            
            content_type = 'application/octet-stream'
            if filename.endswith('.mp4') or filename.endswith('.avi') or filename.endswith('.mov'):
                content_type = 'video/mp4'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif filename.endswith('.png'):
                content_type = 'image/png'
            
            s3_client.upload_file(
                file_path,
                bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'
                }
            )
            
            public_url = f"{endpoint_url.rstrip('/')}/{bucket_name}/{s3_key}"
            
            return public_url
                    
        except Exception as e:
            raise Exception(f"Error uploading file to storage: {str(e)}")
    
    @staticmethod
    def delete_file(file_url):
        try:
            s3_client, bucket_name, _ = StorageService._get_s3_client()
            
            if bucket_name in file_url:
                s3_key = file_url.split(f"{bucket_name}/", 1)[1]
            else:
                s3_key = file_url
            
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            
            return True
                    
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return True
            raise Exception(f"Error deleting file from storage: {str(e)}")
        except Exception as e:
            raise Exception(f"Error deleting file from storage: {str(e)}")
    
    @staticmethod
    def download_file_to_temp(file_url):
        try:
            s3_client, bucket_name, _ = StorageService._get_s3_client()
            
            if bucket_name in file_url:
                s3_key = file_url.split(f"{bucket_name}/", 1)[1]
            else:
                s3_key = file_url
            
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            s3_client.download_file(bucket_name, s3_key, temp_file_path)
            
            return temp_file_path
                    
        except Exception as e:
            raise Exception(f"Error downloading file from storage: {str(e)}")
    
    @staticmethod
    def get_presigned_url(file_url, expiration=3600):
        try:
            s3_client, bucket_name, _ = StorageService._get_s3_client()
            
            if bucket_name in file_url:
                s3_key = file_url.split(f"{bucket_name}/", 1)[1]
            else:
                s3_key = file_url
            
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return presigned_url
                    
        except Exception as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
