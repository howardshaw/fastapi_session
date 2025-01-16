from abc import ABC, abstractmethod
from typing import List, AsyncGenerator

from langchain_core.documents import Document


class DocumentSplitter(ABC):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, **kwargs):
        """
        初始化文档分割器
        
        Args:
            chunk_size: 每个文本块的最大字符数
            chunk_overlap: 相邻文本块之间的重叠字符数
            **kwargs: 其他参数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    async def split(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        """
        将文档分割成更小的片段
        
        Args:
            documents: 要分割的文档列表

        Returns:
            异步生成器，逐个生成分割后的文档片段
        """
        pass
