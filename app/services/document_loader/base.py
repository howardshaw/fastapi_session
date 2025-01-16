import os
import tempfile
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from uuid import UUID

from langchain_core.documents import Document

from app.logger import get_logger
from app.models import Resource
from app.repositories.resource import ResourceRepository
from app.services.storage import StorageService

logger = get_logger(__name__)


class DocumentLoader(ABC):

    def __init__(
            self,
            resource_repository: ResourceRepository,
            storage_service: StorageService,
            **kwargs,
    ):
        self.resource_repository = resource_repository
        self.storage_service = storage_service

    async def load_document(self, resource_id: UUID) -> AsyncGenerator[Document, None]:
        resource = await self.resource_repository.read_by_id(resource_id)
        temp_dir = tempfile.mkdtemp()
        logger.info(f"生成的临时目录路径: {temp_dir}")
        download_path = os.path.join(temp_dir, resource.name)

        await self.storage_service.download(resource.path, download_path)

        # 直接使用 async for 迭代 _process 返回的异步生成器
        async for document in self._process(download_path, resource):
            yield document

    @abstractmethod
    async def _process(self, download_path: str, resource: Resource) -> AsyncGenerator[Document, None]:
        pass
