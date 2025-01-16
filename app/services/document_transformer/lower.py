from typing import AsyncGenerator, List

from langchain_core.documents import Document

from .base import DocumentTransformer


class LowercaseTransformer(DocumentTransformer):
    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        for doc in documents:
            yield Document(page_content=doc.content.lower(), metadata=doc.metadata)
