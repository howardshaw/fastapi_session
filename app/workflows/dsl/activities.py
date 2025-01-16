import uuid
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
from temporalio import activity

from app.logger import get_logger
from app.repositories.resource import ResourceRepository
from app.services.doc_store.base import DocumentStore
from app.services.document_loader import create_loader, LoaderType
from app.services.document_splitter import create_splitter, SplitterType
from app.services.document_transformer import (
    create_transformer,
)
from app.services.embeddings import EmbeddingService
from app.services.storage import StorageService
from app.services.vector_store import create_vector_store, SearchResult
from app.settings import VectorStoreSettings

logger = get_logger(__name__)


class LoadDocumentActivity:
    """资源获取和处理Activity"""

    def __init__(
            self,
            storage_service: StorageService,
            resource_repository: ResourceRepository,
    ):
        self.storage_service = storage_service
        self.resource_repository = resource_repository

    @activity.defn(name="load_document")
    async def run(self, resource_id: str) -> List[Document]:
        if resource_id is None:
            return []
        # 使用工厂方法创建加载器
        loader = create_loader(
            loader_type=LoaderType.LANGCHAIN,
            resource_repository=self.resource_repository,
            storage_service=self.storage_service
        )

        documents = []
        async for doc in loader.load_document(uuid.UUID(resource_id)):
            documents.append(doc)
        logger.info(f"loaded {len(documents)} documents")
        return documents


class SplitDocumentsActivity:
    """文档分块Activity"""

    def __init__(self):
        pass

    @activity.defn(name="split_documents")
    async def run(
            self,
            documents: List[Document],
            chunk_size: int = 1000
    ) -> List[Document]:
        if not documents:
            return []

        logger.info(f"SplitDocumentsActivity for length {len(documents)} {type(documents[0])}")
        # 使用工厂方法创建分割器
        splitter = create_splitter(
            splitter_type=SplitterType.LANGCHAIN,
            chunk_size=chunk_size,
        )

        split_docs = []
        async for doc in splitter.split(documents):
            doc.id = str(uuid.uuid4())
            split_docs.append(doc)
        logger.info(f"split {len(documents)} documents")
        return split_docs


class TransformDocumentsActivity:
    """文档转换Activity"""

    def __init__(
            self,
            llm: Optional[BaseLLM] = None
    ):
        self.llm = llm

    @activity.defn(name="transform_documents")
    async def run(
            self,
            documents: List[Document],
            transformer_type: str,
    ) -> List[Document]:
        if not documents:
            return []
        logger.info(
            f"TransformDocumentsActivity {transformer_type} for length {len(documents)} {type(documents[0])} {documents[0]}")

        # 使用工厂方法创建转换器
        transformer = create_transformer(
            transformer_type=transformer_type,
            llm=self.llm,
        )

        transformed_docs = []
        # document_generator = await transformer.transform(documents)
        async for doc in transformer.transform(documents):
            transformed_docs.append(doc)

        return transformed_docs


class StoreDocumentsActivity:
    """存储文档Activity"""

    def __init__(
            self,
            doc_store: DocumentStore,
            batch_size: int = 50
    ):
        self.doc_store = doc_store
        self.batch_size = batch_size

    @activity.defn(name="store_documents")
    async def run(
            self,
            documents: List[Document],
    ) -> None:
        if not documents:
            return
        logger.info(f"StoreDocumentsActivity for length {len(documents)} {type(documents[0])}")
        batches = [
            documents[i: i + self.batch_size]
            for i in range(0, len(documents), self.batch_size)
        ]

        for idx, batch in enumerate(batches):
            doc_ids = [doc.id for doc in batch if doc.id]
            logger.info(f"Processing batch {idx + 1}/{len(batches)} with {len(batch)} {type(batch[0])} documents.")
            await self.doc_store.amset(list(zip(doc_ids, batch)))


class VectorStoreActivity:
    """向量存储Activity"""

    def __init__(
            self,
            embedding_service: EmbeddingService,
            vector_store_settings: VectorStoreSettings
    ):
        self.embedding_service = embedding_service
        self.vector_store_settings = vector_store_settings

    @activity.defn(name="store_vectors")
    async def run(
            self,
            documents: List[Document],
            collection_name: Optional[str] = None,
    ) -> List[str]:
        if not documents:
            return []

        vector_store = create_vector_store(
            embedding_service=self.embedding_service,
            settings=self.vector_store_settings,
            collection_name=collection_name,
            store_type=self.vector_store_settings.PROVIDER,
        )

        return vector_store.add_documents(documents=documents)


class RetrieveActivity:
    """文档检索Activity"""

    def __init__(
            self,
            doc_store: DocumentStore,
            embedding_service: EmbeddingService,
            vector_store_settings: VectorStoreSettings
    ):
        self.doc_store = doc_store
        self.embedding_service = embedding_service
        self.vector_store_settings = vector_store_settings

    @activity.defn(name="retrieve_documents")
    async def run(
            self,
            query: str,
            collection_name: Optional[str] = None,
            retriever_type: Optional[str] = None,
    ) -> List[SearchResult]:
        vector_store = create_vector_store(
            embedding_service=self.embedding_service,
            settings=self.vector_store_settings,
            collection_name=collection_name,
            store_type=self.vector_store_settings.PROVIDER,
        )

        docs = await vector_store.aretrieve(query, collection_name)
        if not docs:
            return []

        if retriever_type and retriever_type == "multi":
            ids = []
            for d in docs:
                if "doc_id" in d.metadata and d.metadata["doc_id"] not in ids:
                    ids.append(d.metadata["doc_id"])
            docs = self.doc_store.mget(ids)

            return [
                SearchResult(
                    document=doc,
                    score=1,
                    metadata=d.metadata,
                )
                for doc in docs
            ]

        return docs
