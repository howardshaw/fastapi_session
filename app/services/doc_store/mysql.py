import asyncio
from typing import Sequence, Optional

from langchain_community.storage import SQLStore
from langchain_core.documents import Document
from langchain_core.load import dumps, loads

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
        self.store = sql_store

    def mget(self, keys: Sequence[str]) -> list[Optional[Document]]:

        values = self.store.mget(keys)
        return [
            self.value_deserializer(value) if value is not None else value
            for value in values
        ]

    def value_deserializer(self, serialized: bytes) -> bytes:
        return loads(serialized.decode("utf-8"))

    def value_serializer(self, document: Document) -> bytes:
        return dumps(document).encode("utf-8")

    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        if not key_value_pairs:
            return

        try:
            encoded_pairs = [
                (key, self.value_serializer(value))
                for key, value in key_value_pairs
            ]
            logger.debug(f"Encoded pairs keys: {[pair[0] for pair in encoded_pairs]}")
            return self.store.mset(encoded_pairs)
        except Exception as e:
            logger.error(f"Error in mset: {str(e)}")
            logger.error(f"First key-value pair: {key_value_pairs[0] if key_value_pairs else None}")
            raise

    def mdelete(self, keys: Sequence[str]) -> None:
        return self.store.mdelete(keys)
