import os
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import uuid
from typing import Optional, BinaryIO, List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class S3Storage:
    def __init__(self, location: str = '', default_acl: str = 'public-read', file_overwrite: bool = False, custom_domain: Optional[str] = None):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.location = location
        self.default_acl = default_acl
        self.file_overwrite = file_overwrite
        self.custom_domain = custom_domain

    def _get_full_path(self, name: str) -> str:
        if self.location:
            return f"{self.location.rstrip('/')}/{name}"
        return name

    def _generate_unique_filename(self, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        return f"{uuid.uuid4().hex}{ext}"

    def validate_file_type(self, filename: str, content_type: str, allowed_extensions: Optional[List[str]] = None, 
                          allowed_content_types: Optional[List[str]] = None) -> Tuple[bool, str]:
        if not filename:
            return False, "Filename is required"
            
        _, ext = os.path.splitext(filename)
        ext = ext.lower()[1:] if ext.startswith('.') else ext.lower()
        
        if allowed_extensions and ext not in allowed_extensions:
            return False, f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
            
        if allowed_content_types and content_type not in allowed_content_types:
            return False, f"Content type '{content_type}' not allowed. Allowed types: {', '.join(allowed_content_types)}"
            
        return True, ""

    def save(self, file: BinaryIO, name: Optional[str] = None, content_type: Optional[str] = None, 
             allowed_extensions: Optional[List[str]] = None, allowed_content_types: Optional[List[str]] = None) -> str:
        if name is None:
            name = file.filename if hasattr(file, 'filename') else 'unnamed_file'
        
        if allowed_extensions or allowed_content_types:
            is_valid, error_msg = self.validate_file_type(name, content_type, allowed_extensions, allowed_content_types)
            if not is_valid:
                raise ValueError(error_msg)
        
        if not self.file_overwrite:
            name = self._generate_unique_filename(name)
            
        full_path = self._get_full_path(name)
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            
        if self.default_acl:
            extra_args['ACL'] = self.default_acl
        
        try:
            logger.info(f"Uploading file {name} to S3 bucket {self.bucket_name} at path {full_path}")
            self.s3_client.upload_fileobj(file, self.bucket_name, full_path, ExtraArgs=extra_args)
            url = self.get_url(full_path)
            logger.info(f"File uploaded successfully. URL: {url}")
            return url
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    def get_url(self, name: str) -> str:
        if self.custom_domain:
            return f"https://{self.custom_domain}/{name}"
        
        return f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{name}"

    def delete(self, name: str) -> bool:
        try:
            logger.info(f"Deleting file {name} from S3 bucket {self.bucket_name}")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=self._get_full_path(name))
            logger.info(f"File deleted successfully")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {str(e)}")
            return False

class StaticStorage(S3Storage):
    def __init__(self):
        super().__init__(location='static', default_acl='public-read')

class PublicMediaStorage(S3Storage):
    def __init__(self, custom_path: Optional[str] = None):
        location = 'public'
        if custom_path:
            location = f"public/{custom_path}"
        super().__init__(location=location, default_acl='public-read', file_overwrite=False)

class PrivateMediaStorage(S3Storage):
    def __init__(self, custom_path: Optional[str] = None):
        location = 'private'
        if custom_path:
            location = f"private/{custom_path}"
        super().__init__(location=location, default_acl='private', file_overwrite=False, custom_domain=None)