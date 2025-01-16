from typing import AsyncGenerator, List

from langchain_core.documents import Document

from .base import DocumentTransformer


class PrefixTransformer(DocumentTransformer):
    def __init__(self, prefix: str, **kwargs):
        super().__init__(**kwargs)
        self.prefix = prefix

    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        for doc in documents:
            yield Document(page_content=f"{self.prefix}{doc.content}", metadata=doc.metadata)
