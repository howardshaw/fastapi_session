import uuid
from typing import Callable, Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import get_logger
from app.models.dataset import Dataset
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class DatasetRepository(BaseRepository):
    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        super().__init__(session_or_factory, Dataset)

    async def create_dataset(self, dataset: Dataset) -> Dataset:
        """创建知识库"""
        logger.info(f"Creating dataset: {dataset}")
        return await super().create(dataset)

    async def get_workspace_datasets(
            self,
            workspace_id: uuid.UUID,
            *,
            skip: int = 0,
            limit: int = 100
    ) -> List[Dataset]:
        """获取工作空间下的知识库列表"""
        query = self.filter(workspace_id=str(workspace_id))
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_dataset(self, dataset_id: uuid.UUID) -> Optional[Dataset]:
        """获取特定知识库"""
        query = self.filter(id=str(dataset_id))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_dataset(
            self,
            user_id: uuid.UUID,
            dataset_id: uuid.UUID,
            workspace_id: Optional[uuid.UUID] = None
    ) -> Optional[Dataset]:
        """获取用户的特定知识库"""
        query = self.filter(id=str(dataset_id), user_id=str(user_id))
        if workspace_id:
            query = query.filter(Dataset.workspace_id == str(workspace_id))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_dataset(self, dataset_id: uuid.UUID, dataset_data: dict) -> Optional[Dataset]:
        """更新知识库"""
        dataset = await self.get_dataset(dataset_id)
        if dataset:
            for key, value in dataset_data.items():
                setattr(dataset, key, value)
            await self.session.commit()
            await self.session.refresh(dataset)
        return dataset

    async def delete_dataset(self, dataset_id: uuid.UUID) -> Optional[Dataset]:
        """删除知识库"""
        dataset = await self.get_dataset(dataset_id)
        if dataset:
            await self.session.delete(dataset)
            await self.session.commit()
        return dataset

    async def count_workspace_datasets(self, workspace_id: uuid.UUID) -> int:
        """统计工作空间下的知识库数量"""
        query = select(func.count()).select_from(Dataset).where(
            Dataset.workspace_id == str(workspace_id)
        )
        result = await self.session.execute(query)
        return result.scalar() or 0 