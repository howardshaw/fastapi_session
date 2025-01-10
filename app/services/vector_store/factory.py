from typing import Literal, Optional

from app.services.embeddings import EmbeddingService
from app.settings import VectorStoreSettings
from .base import VectorStoreService
from .chroma import ChromaVectorStore
from .milvus import MilvusVectorStore
from .opensearch import OpenSearchVectorStore

VectorStoreType = Literal["chroma", "milvus", "opensearch"]


def create_vector_store(
        embedding_service: EmbeddingService,
        settings: VectorStoreSettings,
        collection_name: str,
        store_type: Optional[VectorStoreType],
) -> VectorStoreService:
    """
    创建向量存储服务的工厂方法
    
    Args:
        store_type: 向量存储类型，支持 "chroma"、"milvus" 或 "opensearch"
        embedding_service: 嵌入服务实例
        settings: 向量存储配置
        collection_name: collection名字
        
    Returns:
        VectorStoreService: 向量存储服务实例
        
    Raises:
        ValueError: 当提供的store_type不支持时
    """
    store_map = {
        "chroma": ChromaVectorStore,
        "milvus": MilvusVectorStore,
        "opensearch": OpenSearchVectorStore
    }
    if not store_type:
        store_type = settings.PROVIDER
    if store_type not in store_map:
        raise ValueError(f"Unsupported vector store type: {store_type}. "
                         f"Supported types are: {list(store_map.keys())}")

    store_class = store_map[store_type]
    return store_class(embedding_service=embedding_service, settings=settings, collection_name=collection_name)
