import os
import tempfile
import uuid
from typing import List, Optional

from langchain_core.documents import Document
from temporalio import activity

from app.logger import get_logger
from app.repositories.resource import ResourceRepository
from app.services.doc_store.base import DocumentStore
from app.services.document_processor import DocumentProcessor
from app.services.document_transform import (
    ContentCleanTransformer,
    ChunkSplitTransformer,
    HypotheticalQuestionTransformer,
    SummaryTransformer
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
            document_processor: DocumentProcessor
    ):
        self.storage_service = storage_service
        self.resource_repository = resource_repository
        self.document_processor = document_processor

    @activity.defn(name="load_document")
    async def run(self, resource_id: str) -> List[Document]:
        """获取资源并直接处理成文档"""
        # 获取资源
        resource = await self.resource_repository.read_by_id(uuid.UUID(resource_id))
        # 创建一个临时随机目录
        temp_dir = tempfile.mkdtemp()
        logger.info(f"生成的临时目录路径: {temp_dir}")

        # 创建临时文件的路径
        file_name = "downloaded_file.pdf"
        download_path = os.path.join(temp_dir, resource.name)

        await self.storage_service.download(resource.path, download_path)

        # 直接处理成文档
        documents = await self.document_processor.process(download_path, resource.mime_type)

        # TODO 如果文档太大

        return documents


class CleanContentActivity:
    """内容清理Activity"""

    def __init__(self, transformer: ContentCleanTransformer):
        self.transformer = transformer

    @activity.defn(name="clean_content")
    async def run(self, documents: List[Document]) -> List[Document]:
        if len(documents) == 0:
            return []
        return await self.transformer.transform(documents)


class StoreDocumentsActivity:
    """存储文档Activity"""

    def __init__(
            self,
            doc_store: DocumentStore,
            batch_size: int = 100
    ):
        self.doc_store = doc_store
        self.batch_size = batch_size

    @activity.defn(name="store_documents")
    async def run(
            self,
            documents: List[Document],
    ) -> None:
        if len(documents) == 0:
            return
        logger.info(f"store document for {len(documents)} documents {type(documents[0])} {documents[0]}")

        batches = [
            documents[i: i + self.batch_size]
            for i in range(0, len(documents), self.batch_size)
        ]

        for idx, batch in enumerate(batches):
            doc_ids = [doc.id for doc in batch]
            logger.info(f"Processing batch {idx + 1}/{len(batches)} with {len(batch)} {type(batch[0])} documents.")
            await self.doc_store.amset(list(zip(doc_ids, batch)))

        logger.info("All documents have been successfully stored.")
        return


class SplitDocumentsActivity:
    """文档分块Activity"""

    def __init__(
            self,
            transformer: ChunkSplitTransformer
    ):
        self.transformer = transformer

    @activity.defn(name="split_documents")
    async def run(
            self,
            documents: List[Document],
            chunk_size: int = 1000
    ) -> List[Document]:
        if len(documents) == 0:
            return []
        logger.info(f"split document for {len(documents)} documents {type(documents[0])} {documents[0]}")
        self.transformer.chunk_size = chunk_size
        res = await self.transformer.transform(documents)
        if len(res) == 0:
            return []
        logger.info(f"split document result for {len(res)}  {type(res[0])} {res[0]}")
        return res[:2]


class HypotheticalQuestionActivity:
    """生成假设问Activity"""

    def __init__(self, transformer: HypotheticalQuestionTransformer):
        self.transformer = transformer

    @activity.defn(name="hypothetical_question")
    async def run(self, documents: List[Document]) -> List[Document]:
        if len(documents) == 0:
            return []
        return await self.transformer.transform(documents)


class GenerateSummaryActivity:
    """摘要生成Activity"""

    def __init__(self, transformer: SummaryTransformer):
        self.transformer = transformer

    @activity.defn(name="generate_summary")
    async def run(self, documents: List[Document]) -> List[Document]:
        if len(documents) == 0:
            return []
        logger.info(f"generating summary for {len(documents)} documents {type(documents[0])} {documents[0]}")
        return await self.transformer.transform(documents)


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
        """
        将文档存储到向量数据库
        
        Args:
            splits: 要存储的文档列表
            collection_name: 集合名称
            store_type: 向量存储类型，支持 "chroma"、"milvus" 或 "opensearch"
            
        Returns:
            List[str]: 存储的文档ID列表
        """
        if len(documents) == 0:
            return []
        logger.info(f"store document  for {len(documents)} documents {type(documents[0])} {documents[0]}")

        vector_store = create_vector_store(
            embedding_service=self.embedding_service,
            settings=self.vector_store_settings,
            collection_name=collection_name,
            store_type=self.vector_store_settings.PROVIDER,
        )

        return vector_store.add_documents(
            documents=documents,
        )


class RetrieveActivity:
    """向量存储Activity"""

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

        logger.info(f"retrieve documents for {query} in collection {collection_name}")
        docs = await vector_store.aretrieve(query, collection_name)
        if len(docs) == 0:
            return []
        if retriever_type and retriever_type == "multi":
            logger.info(f"retrieved documents for {len(docs)} in collection {collection_name} {docs[0]}")
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
