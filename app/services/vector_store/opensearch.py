from typing import List, Dict, Any, Optional

from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_core.documents import Document
from opensearchpy import RequestsHttpConnection

from app.logger import get_logger
from app.services.embeddings import EmbeddingService, LangChainedEmbeddingWrapper
from app.settings import VectorStoreSettings
from .base import VectorStoreService, SearchResult

logger = get_logger(__name__)


class OpenSearchVectorStore(VectorStoreService):
    """OpenSearch向量存储实现"""

    def __init__(
            self,
            embedding_service: EmbeddingService,
            settings: VectorStoreSettings,
            collection_name: Optional[str] = None
    ):
        logger.info(f"Setting up opensearch {settings.OPENSEARCH_HOSTS}")

        # 配置连接参数
        opensearch_url = f"https://{settings.OPENSEARCH_HOSTS[0]}" if settings.OPENSEARCH_USE_SSL else f"http://{settings.OPENSEARCH_HOSTS[0]}"

        # 设置认证
        http_auth = None
        if settings.OPENSEARCH_USER:
            http_auth = (settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD)

        # Initialize OpenSearchVectorSearch first
        self._store = OpenSearchVectorSearch(
            index_name=collection_name or settings.COLLECTION_NAME,
            embedding_function=LangChainedEmbeddingWrapper(embedding_service),
            opensearch_url=opensearch_url,
            http_auth=http_auth,
            use_ssl=settings.OPENSEARCH_USE_SSL,
            verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
            connection_class=RequestsHttpConnection,
            engine="nmslib",  # 或 "faiss"
        )

    def add_documents(
            self, documents: list[Document], **kwargs: Any
    ) -> list[str]:
        return self._store.add_documents(documents, **kwargs)

    async def aadd_documents(
            self, documents: list[Document], **kwargs: Any
    ) -> list[str]:
        return await self._store.aadd_documents(documents, **kwargs)

    async def aretrieve(
            self,
            query: str,
            collection_name: str,
            top_k: int = 10,
            filter: Optional[Dict[str, Any]] = None,
            hybrid_search: bool = False,
            **kwargs
    ) -> List[SearchResult]:
        if hybrid_search:
            raise NotImplementedError("Hybrid search not supported in OpenSearch integration")

        results = await self._store.asimilarity_search_with_score(
            query,
            k=top_k,
            filter=filter,
            **kwargs
        )

        return [
            SearchResult(
                document=doc,
                score=score,
                metadata=doc.metadata
            )
            for doc, score in results
        ]

    def retrieve(
            self,
            query: str,
            collection_name: str,
            top_k: int = 10,
            filter: Optional[Dict[str, Any]] = None,
            hybrid_search: bool = False,
            **kwargs
    ) -> List[SearchResult]:
        if hybrid_search:
            raise NotImplementedError("Hybrid search not supported in OpenSearch integration")
        logger.info(f"Retrieving {query} from OpenSearch {collection_name}")
        results = self._store.similarity_search_with_score(
            query,
            k=top_k,
            filter=filter,
            **kwargs
        )

        return [
            SearchResult(
                document=doc,
                score=score,
                metadata=doc.metadata
            )
            for doc, score in results
        ]
