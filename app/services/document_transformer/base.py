from abc import ABC, abstractmethod
from typing import AsyncGenerator, List

from langchain_core.documents import Document


class DocumentTransformer(ABC):
    def __init__(self, **kwargs):
        """
        初始化文档转换器
        
        Args:
            **kwargs: 转换器的配置参数
        """
        self.kwargs = kwargs

    @abstractmethod
    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        """
        对文档进行转换处理
        
        Args:
            documents: 要处理的文档列表

        Returns:
            转换后的文档生成器
        """
        pass
