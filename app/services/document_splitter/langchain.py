from typing import List, Optional, Type, Dict, AsyncGenerator

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    RecursiveJsonSplitter,
)

from .base import DocumentSplitter


class LangChainSplitter(DocumentSplitter):
    # 定义不同类型文档的默认分割器
    SPLITTER_MAP: Dict[str, Type] = {
        # 通用文本
        "text/plain": RecursiveCharacterTextSplitter,

        # 特定格式文本
        "text/markdown": MarkdownTextSplitter,
        "text/python": PythonCodeTextSplitter,
        "application/json": RecursiveJsonSplitter,

        # 默认分割器
        "default": RecursiveCharacterTextSplitter
    }

    def __init__(
            self,
            chunk_size: int = 1000,
            chunk_overlap: int = 200,
            mime_type: Optional[str] = None,
            **kwargs
    ):
        """
        初始化 LangChain 文档分割器
        
        Args:
            chunk_size: 每个文本块的最大字符数
            chunk_overlap: 相邻文本块之间的重叠字符数
            mime_type: 文档的 MIME 类型，用于选择合适的分割器
            **kwargs: 传递给具体分割器的其他参数
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap, **kwargs)
        self.mime_type = mime_type
        self.kwargs = kwargs

    def _get_splitter(self):
        """获取适合当前文档类型的分割器"""
        splitter_cls = self.SPLITTER_MAP.get(
            self.mime_type,
            self.SPLITTER_MAP["default"]
        )

        return splitter_cls(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            **self.kwargs
        )

    async def split(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        """
        使用 LangChain 的文本分割器将文档分割成更小的片段
        
        Args:
            documents: 要分割的文档列表

        Yields:
            分割后的文档片段
        """
        try:
            splitter = self._get_splitter()

            for doc in documents:
                # 保留原文档的 metadata
                chunks = splitter.split_text(doc.page_content)
                for i, chunk in enumerate(chunks):
                    yield Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )

        except Exception as e:
            raise ValueError(f"Error splitting documents: {str(e)}")
