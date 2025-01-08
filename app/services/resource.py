import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Database
from app.core.exceptions import DatabaseError
from app.logger import get_logger
from app.models.resource import Resource, StorageType
from app.repositories.resource import ResourceRepository
from app.services.storage.base import StorageService
from app.utils.mime import get_resource_type_from_mime

logger = get_logger(__name__)


class ResourceService:
    def __init__(
            self,
            db: Database,
            resource_repository: ResourceRepository,
            storage_service: StorageService
    ):
        self.db = db
        self.repository = resource_repository
        self.storage = storage_service

    async def upload_resource(
            self,
            file: UploadFile,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID,
            meta_info: Optional[Dict] = None,
            storage_type: StorageType = StorageType.MINIO,
    ) -> Resource:
        """
        上传资源文件
        
        Args:
            file: 上传的文件
            workspace_id: 工作空间ID
            user_id: 用户ID
            meta_info: 元信息
            storage_type: 存储类型
            
        Returns:
            Resource: 创建的资源对象
        """
        # 生成存储路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{workspace_id}/{timestamp}_{file.filename}"

        # 上传文件
        stored_path = await self.storage.upload_file(
            file=file.file,
            path=path,
            content_type=file.content_type
        )

        # 创建资源记录
        resource = Resource(
            name=file.filename,
            storage_type=storage_type,
            resource_type=get_resource_type_from_mime(file.content_type),
            size=file.size,
            path=stored_path,
            mime_type=file.content_type,
            meta_info=meta_info,
            workspace_id=workspace_id,
            user_id=user_id
        )

        try:
            async with self.db.transaction():
                await self.repository.create(resource)
        except SQLAlchemyError as e:
            logger.error(f"Database error during create resource: {str(e)}")
            raise DatabaseError(f"Failed to save resource with file {file.filename}")

        return resource

    async def get_workspace_resources(
            self,
            workspace_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100
    ) -> list[Resource]:
        """获取工作空间的资源列表"""
        return await self.repository.get_workspace_resources(workspace_id, skip=skip, limit=limit)

    async def get_resource(
            self,
            resource_id: uuid.UUID,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> Optional[Resource]:
        """获取特定资源"""
        return await self.repository.get_user_resource(resource_id, workspace_id, user_id)

    async def delete_resource(
            self,
            resource_id: uuid.UUID,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> bool:
        """删除资源"""
        resource = await self.get_resource(resource_id, workspace_id, user_id)
        if not resource:
            return False

        # 删除存储的文件
        if await self.storage.delete_file(resource.path):
            # 删除数据库记录
            await self.repository.delete(resource)
            return True
        return False

    async def get_resource_url(
            self,
            resource_id: uuid.UUID,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID,
            expire: timedelta
    ) -> Optional[str]:
        """
        获取资源的访问URL
        
        Args:
            resource_id: 资源ID
            workspace_id: 工作空间ID
            user_id: 用户ID
            expire: URL过期时间(秒)
            
        Returns:
            str: 资源访问URL，如果资源不存在返回None
        """
        resource = await self.repository.get_user_resource(
            resource_id=resource_id,
            workspace_id=workspace_id,
            user_id=user_id
        )

        if not resource:
            return None

        return await self.storage.get_file_url(resource.path, expire)

    async def get_resource_urls(
            self,
            resources: list[Resource],
            expire: int = 3600
    ) -> Dict[uuid.UUID, str]:
        """
        批量获取资源的访问URL
        
        Args:
            resources: 资源列表
            expire: URL过期时间(秒)
            
        Returns:
            Dict[uuid.UUID, str]: 资源ID到URL的映射
        """
        urls = {}
        for resource in resources:
            urls[resource.id] = await self.storage.get_file_url(
                resource.path,
                expire
            )
        return urls

    async def get_workspace_resources_with_urls(
            self,
            workspace_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100,
            expire: int = 3600
    ) -> tuple[list[Resource], Dict[uuid.UUID, str], int]:
        """
        获取工作空间的资源列表及其URL
        
        Args:
            workspace_id: 工作空间ID
            skip: 跳过记录数
            limit: 返回记录数限制
            expire: URL过期时间(秒)
            
        Returns:
            tuple: (资源列表, URL映射, 总数)
        """
        resources = await self.repository.get_workspace_resources(
            workspace_id,
            skip=skip,
            limit=limit
        )
        total = await self.repository.count_workspace_resources(workspace_id)
        urls = await self.get_resource_urls(resources, expire)

        return resources, urls, total
