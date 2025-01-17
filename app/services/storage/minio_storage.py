from typing import BinaryIO, Optional, Dict, Union
from datetime import timedelta
from minio import Minio
from minio.error import MinioException

from app.settings import StorageSettings
from app.logger import get_logger
from .base import StorageService

logger = get_logger(__name__)


class MinioStorageService(StorageService):
    def __init__(self, settings: StorageSettings):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """确保 bucket 存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except MinioException as e:
            logger.error(f"Failed to ensure bucket: {e}")
            raise

    async def upload_file(
        self,
        file: BinaryIO,
        path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        try:
            # 获取文件大小
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)

            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=path,
                data=file,
                length=size,
                content_type=content_type,
                metadata=metadata
            )
            return path
        except MinioException as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def delete_file(self, path: str) -> bool:
        try:
            self.client.remove_object(self.bucket, path)
            return True
        except MinioException as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    async def get_file_url(self, path: str, expire: timedelta = timedelta(days=7)) -> str:
        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=path,
                expires=expire
            )
        except MinioException as e:
            logger.error(f"Failed to get file url: {e}")
            raise 

    async def download(self, source_path: str, dest_path: str) -> None:
        try:
            return self.client.fget_object(self.bucket, source_path, dest_path)
        except MinioException as e:
            logger.error(f"Failed to get file content: {e}")
            raise 