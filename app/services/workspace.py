import uuid
from typing import List, Optional

from app.core.database import Database
from app.logger import get_logger
from app.models.workspace import Workspace
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from sqlalchemy.sql import select, func

logger = get_logger(__name__)


class WorkspaceService:
    def __init__(self, db: Database, workspace_repository: WorkspaceRepository):
        self.db = db
        self.workspace_repository = workspace_repository

    async def create_workspace(self, workspace_data: WorkspaceCreate, user_id: uuid.UUID) -> Workspace:
        """
        创建工作空间
        """
        async with self.db.transaction():
            workspace_dict = workspace_data.model_dump()
            workspace_dict["user_id"] = user_id
            workspace = await self.workspace_repository.create_workspace(
                Workspace(**workspace_dict)
            )
            logger.info(f"Created workspace with id: {workspace.id}")
            return workspace

    async def get_user_workspace(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> Optional[Workspace]:
        """
        获取用户的特定工作空间
        """
        return await self.workspace_repository.get_user_workspace(user_id, workspace_id)

    async def get_user_workspaces(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Workspace]:
        """
        获取用户的工作空间列表
        """
        return await self.workspace_repository.get_user_workspaces(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

    async def update_workspace(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, workspace_data: WorkspaceUpdate
    ) -> Optional[Workspace]:
        """
        更新工作空间
        """
        async with self.db.transaction():
            # 验证工作空间归属
            workspace = await self.workspace_repository.get_user_workspace(
                user_id, workspace_id
            )
            if not workspace:
                return None

            # 更新工作空间
            updated_workspace = await self.workspace_repository.update_workspace(
                workspace_id,
                workspace_data.model_dump(exclude_unset=True)
            )
            logger.info(f"Updated workspace with id: {workspace_id}")
            return updated_workspace

    async def delete_workspace(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> Optional[Workspace]:
        """
        删除工作空间
        """
        async with self.db.transaction():
            # 验证工作空间归属
            workspace = await self.workspace_repository.get_user_workspace(
                user_id, workspace_id
            )
            if not workspace:
                return None

            # 删除工作空间
            deleted_workspace = await self.workspace_repository.delete_workspace(workspace_id)
            logger.info(f"Deleted workspace with id: {workspace_id}")
            return deleted_workspace

    async def count_user_workspaces(self, user_id: uuid.UUID) -> int:
        """
        统计用户拥有的工作空间数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 工作空间总数
        """
        return await self.workspace_repository.count_user_workspaces(user_id)
