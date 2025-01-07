import uuid
from typing import Callable, Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import get_logger
from app.models.workspace import Workspace
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class WorkspaceRepository(BaseRepository):
    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        self._session_or_factory = session_or_factory
        super().__init__(session_or_factory, Workspace)

    async def create_workspace(self, workspace: Workspace) -> Workspace:
        """
        创建工作空间
        
        Args:
            workspace: 工作空间对象
            
        Returns:
            创建的工作空间
        """
        logger.info(f"Creating workspace: {workspace}")
        return await super().create(workspace)

    async def get_user_workspaces(
            self,
            user_id: uuid.UUID,
            *,
            skip: int = 0,
            limit: int = 100
    ) -> List[Workspace]:
        """
        获取用户的工作空间列表
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            工作空间列表
        """
        query = self.filter(user_id=str(user_id))
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_workspace(self, workspace_id: uuid.UUID) -> Optional[Workspace]:
        """
        获取特定工作空间
        
        Args:
            workspace_id: 工作空间ID
            
        Returns:
            工作空间对象，如果不存在返回 None
        """
        query = self.filter(id=str(workspace_id))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_workspace(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> Optional[Workspace]:
        """
        获取用户的特定工作空间
        
        Args:
            user_id: 用户ID
            workspace_id: 工作空间ID
            
        Returns:
            工作空间对象，如果不存在返回 None
        """
        query = self.filter(id=str(workspace_id), user_id=str(user_id))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_workspace(self, workspace_id: uuid.UUID, workspace_data: dict) -> Optional[Workspace]:
        """
        更新工作空间
        
        Args:
            workspace_id: 工作空间ID
            workspace_data: 更新的数据
            
        Returns:
            更新后的工作空间对象，如果不存在返回 None
        """
        workspace = await self.get_workspace(workspace_id)
        if workspace:
            for key, value in workspace_data.items():
                setattr(workspace, key, value)
            await self.session.commit()
            await self.session.refresh(workspace)
        return workspace

    async def delete_workspace(self, workspace_id: uuid.UUID) -> Optional[Workspace]:
        """
        删除工作空间
        
        Args:
            workspace_id: 工作空间ID
            
        Returns:
            被删除的工作空间对象，如果不存在返回 None
        """
        workspace = await self.get_workspace(workspace_id)
        if workspace:
            await self.session.delete(workspace)
            await self.session.commit()
        return workspace

    async def count_user_workspaces(self, user_id: uuid.UUID) -> int:
        """
        统计用户拥有的工作空间数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 工作空间总数
        """
        query = select(func.count()).select_from(Workspace).where(
            Workspace.user_id == str(user_id),
        )

        result = await self.session.execute(query)
        return result.scalar() or 0
