from typing import List, Dict, Any, Optional

from langchain_chroma import Chroma as LangChainChroma
from langchain_core.documents import Document

from app.services.embeddings.base import EmbeddingService, LangChainedEmbeddingWrapper
from app.settings import VectorStoreSettings
from .base import VectorStoreService, SearchResult


class ChromaVectorStore(VectorStoreService):
    """Chroma向量存储实现"""

    def __init__(
            self,
            embedding_service: EmbeddingService,
            settings: VectorStoreSettings,
            collection_name: Optional[str] = None
    ):
        self._store = LangChainChroma(
            collection_name=collection_name or settings.COLLECTION_NAME,
            embedding_function=LangChainedEmbeddingWrapper(embedding_service),
            persist_directory=settings.CHROMA_PERSIST_DIR
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
