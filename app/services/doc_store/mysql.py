import asyncio
from typing import Sequence, Optional

from langchain.storage import create_kv_docstore
from langchain_community.storage import SQLStore
from langchain_core.documents import Document

from app.logger import get_logger
from app.settings import DocumentStoreSettings
from .base import DocumentStore

logger = get_logger(__name__)


class MySQLDocumentStore(DocumentStore):
    def __init__(self, settings: DocumentStoreSettings):
        sql_store = SQLStore(
            namespace=settings.NAMESPACE,
            db_url=settings.URL,
            async_mode=settings.ASYNC_MODE,
        )
        if settings.ASYNC_MODE:
            logger.info(f"start to create mysql store schema async")
            asyncio.run(sql_store.acreate_schema())
        else:
            logger.info(f"start to create mysql store schema")
            sql_store.create_schema()
        self.store = create_kv_docstore(sql_store)

    def mget(self, keys: Sequence[str]) -> list[Optional[Document]]:
        return self.store.mget(keys)

    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        logger.info(f"MySQLDocumentStore try to set {key_value_pairs}")
        return self.store.mset(key_value_pairs)

    def mdelete(self, keys: Sequence[str]) -> None:
        return self.store.mdelete(keys)
