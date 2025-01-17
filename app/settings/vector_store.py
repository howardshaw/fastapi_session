from typing import Optional, List

from pydantic_settings import BaseSettings, SettingsConfigDict


class VectorStoreSettings(BaseSettings):
    PROVIDER: str = "opensearch"  # chroma, milvus, opensearch
    COLLECTION_NAME: str = "vector"

    # Chroma settings
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Milvus settings
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""

    # OpenSearch settings
    OPENSEARCH_HOSTS: List[str] = ["localhost:9200"]
    OPENSEARCH_USER: Optional[str] = None
    OPENSEARCH_PASSWORD: Optional[str] = None
    OPENSEARCH_USE_SSL: bool = False
    OPENSEARCH_VERIFY_CERTS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VECTOR_STORE__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )
