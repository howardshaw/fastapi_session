from typing import AsyncGenerator, Dict, Type

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
)
from langchain_core.documents import Document

from app.models import Resource
from app.repositories.resource import ResourceRepository
from app.services.storage import StorageService
from .base import DocumentLoader


class LangChainLoader(DocumentLoader):
    # 定义支持的 MIME 类型到加载器的映射
    LOADER_MAP: Dict[str, Type] = {
        # PDF文件
        "application/pdf": PyPDFLoader,

        # 文本文件
        "text/plain": TextLoader,
        "text/csv": CSVLoader,

        # Microsoft Office 文件
        "application/msword": UnstructuredWordDocumentLoader,  # .doc
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": UnstructuredWordDocumentLoader,
        # .docx
        "application/vnd.ms-powerpoint": UnstructuredPowerPointLoader,  # .ppt
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": UnstructuredPowerPointLoader,
        # .pptx
        "application/vnd.ms-excel": UnstructuredExcelLoader,  # .xls
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": UnstructuredExcelLoader,  # .xlsx
    }

    def __init__(
            self,
            resource_repository: ResourceRepository,
            storage_service: StorageService,
            **kwargs,
    ):
        super().__init__(resource_repository, storage_service, **kwargs)

    async def _process(self, download_path: str, resource: Resource) -> AsyncGenerator[Document, None]:
        loader_cls = self.LOADER_MAP.get(resource.mime_type)
        if not loader_cls:
            raise ValueError(f"Unsupported mime type: {resource.mime_type}")

        try:
            loader = loader_cls(file_path=download_path)
            # 某些加载器可能没有 alazy_load 方法，需要处理这种情况
            if hasattr(loader, 'alazy_load'):
                async for document in loader.alazy_load():
                    yield document
            else:
                # 对于不支持异步加载的加载器，同步加载所有文档
                for document in loader.load():
                    yield document

        except Exception as e:
            raise ValueError(f"Error loading document: {str(e)}")
