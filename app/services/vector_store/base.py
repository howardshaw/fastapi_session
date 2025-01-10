from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_core.runnables import run_in_executor

from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float
    metadata: Dict[str, Any]


class VectorStoreService(ABC):
    """向量存储服务基类"""

    async def aadd_documents(
            self, documents: list[Document], **kwargs: Any
    ) -> list[str]:
        return await run_in_executor(None, self.add_documents, documents, kwargs)

    @abstractmethod
    def add_documents(
            self, documents: list[Document], **kwargs: Any
    ) -> list[str]:
        pass

    @abstractmethod
    def retrieve(
            self,
            query: str,
            collection_name: str,
            top_k: int = 10,
            filter: Optional[Dict[str, Any]] = None,
            hybrid_search: bool = False,
            **kwargs
    ) -> List[SearchResult]:
        """检索相似文档"""
        pass

    @abstractmethod
    async def aretrieve(
            self,
            query: str,
            collection_name: str,
            top_k: int = 10,
            filter: Optional[Dict[str, Any]] = None,
            hybrid_search: bool = False,
            **kwargs
    ) -> List[SearchResult]:
        """检索相似文档"""
        return await run_in_executor(None, self.retrieve, query, collection_name, top_k, filter, hybrid_search, kwargs)
