from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document


class DocumentProcessor(ABC):
    """文档处理基类"""

    @abstractmethod
    async def process(self, content: str, mime_type: str) -> List[Document]:
        """处理文档内容"""
        pass


class LangchainDocumentProcessor(DocumentProcessor):
    def __init__(self):
        # from langchain_community.document_loaders import UnstructuredPDFLoader, TextLoader
        from langchain_community.document_loaders import PyPDFLoader, TextLoader
        self.loader_map = {
            "application/pdf": PyPDFLoader,
            "text/plain": TextLoader
        }

    async def process(self, content: str, mime_type: str) -> List[Document]:
        loader_cls = self.loader_map.get(mime_type)
        if not loader_cls:
            raise ValueError(f"Unsupported mime type: {mime_type}")

        loader = loader_cls(content)
        return await loader.aload()
