import uuid
from typing import List, Optional

from fastapi import HTTPException

from app.core.database import Database
from app.models.dataset import Dataset
from app.repositories.dataset import DatasetRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.dataset import DatasetCreate, DatasetUpdate


class DatasetService:
    def __init__(
            self,
            db: Database,
            dataset_repository: DatasetRepository,
            workspace_repository: WorkspaceRepository
    ):
        self.db = db
        self.dataset_repository = dataset_repository
        self.workspace_repository = workspace_repository

    async def verify_workspace_access(
            self,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> None:
        """验证工作空间访问权限"""
        workspace = await self.workspace_repository.get_user_workspace(
            user_id=user_id,
            workspace_id=workspace_id
        )
        if not workspace:
            raise HTTPException(
                status_code=404,
                detail="Workspace not found or you don't have access to it"
            )

    async def create_dataset(
            self,
            dataset_create: DatasetCreate,
            user_id: uuid.UUID
    ) -> Dataset:
        """创建知识库"""
        # 验证工作空间访问权限
        await self.verify_workspace_access(dataset_create.workspace_id, user_id)

        dataset = Dataset(
            name=dataset_create.name,
            description=dataset_create.description,
            icon=dataset_create.icon,
            type=dataset_create.type,
            config=dataset_create.config,
            workspace_id=dataset_create.workspace_id,
            user_id=user_id
        )
        async with self.db.transaction():
            return await self.dataset_repository.create_dataset(dataset)

    async def get_workspace_datasets(
            self,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID,
            skip: int = 0,
            limit: int = 100
    ) -> List[Dataset]:
        """获取工作空间下的知识库列表"""
        # 验证工作空间访问权限
        await self.verify_workspace_access(workspace_id, user_id)

        return await self.dataset_repository.get_workspace_datasets(
            workspace_id,
            skip=skip,
            limit=limit
        )

    async def get_user_dataset(
            self,
            user_id: uuid.UUID,
            dataset_id: uuid.UUID,
            workspace_id: Optional[uuid.UUID] = None
    ) -> Optional[Dataset]:
        """获取用户的特定知识库"""
        if workspace_id:
            # 如果提供了workspace_id，先验证访问权限
            await self.verify_workspace_access(workspace_id, user_id)

        return await self.dataset_repository.get_user_dataset(
            user_id,
            dataset_id,
            workspace_id
        )

    async def update_dataset(
            self,
            user_id: uuid.UUID,
            dataset_id: uuid.UUID,
            dataset_update: DatasetUpdate
    ) -> Optional[Dataset]:
        """更新知识库"""
        dataset = await self.get_user_dataset(user_id, dataset_id)
        if dataset:
            # 验证工作空间访问权限
            await self.verify_workspace_access(dataset.workspace_id, user_id)

            update_data = dataset_update.model_dump(exclude_unset=True)
            async with self.db.transaction():
                return await self.dataset_repository.update_dataset(
                    dataset_id,
                    update_data
                )
        return None

    async def delete_dataset(
            self,
            user_id: uuid.UUID,
            dataset_id: uuid.UUID
    ) -> Optional[Dataset]:
        """删除知识库"""
        dataset = await self.get_user_dataset(user_id, dataset_id)
        if dataset:
            # 验证工作空间访问权限
            await self.verify_workspace_access(dataset.workspace_id, user_id)
            async with self.db.transaction():
                return await self.dataset_repository.delete_dataset(dataset_id)
        return None

    async def count_workspace_datasets(
            self,
            workspace_id: uuid.UUID,
            user_id: uuid.UUID
    ) -> int:
        """统计工作空间下的知识库数量"""
        # 验证工作空间访问权限
        await self.verify_workspace_access(workspace_id, user_id)

        return await self.dataset_repository.count_workspace_datasets(workspace_id)
