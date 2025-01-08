import uuid
from typing import List, Optional, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import get_logger
from app.models.resource import Resource
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ResourceRepository(BaseRepository):
    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        super().__init__(session_or_factory, Resource)

    async def get_workspace_resources(
        self,
        workspace_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Resource]:
        """
        获取工作空间的资源列表
        
        Args:
            workspace_id: 工作空间ID
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            资源列表
        """
        query = self.filter(workspace_id=str(workspace_id))
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user_resource(
        self,
        resource_id: uuid.UUID,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[Resource]:
        """
        获取用户在特定工作空间的资源
        
        Args:
            resource_id: 资源ID
            workspace_id: 工作空间ID
            user_id: 用户ID
            
        Returns:
            资源对象，如果不存在返回 None
        """
        query = self.filter(
            id=str(resource_id),
            workspace_id=str(workspace_id),
            user_id=str(user_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_workspace_resources(self, workspace_id: uuid.UUID) -> int:
        """
        统计工作空间的资源总数
        
        Args:
            workspace_id: 工作空间ID
            
        Returns:
            资源总数
        """
        query = select(self.model).filter_by(workspace_id=str(workspace_id))
        result = await self.session.execute(query)
        return len(result.scalars().all()) 