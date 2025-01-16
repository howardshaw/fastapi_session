from typing import AsyncGenerator, List

from langchain_core.documents import Document

from .base import DocumentTransformer


class CleanTransformer(DocumentTransformer):
    """内容清理"""

    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        for doc in documents:
            cleaned_text = (doc.page_content
                            .strip()
                            .replace('\n\n', '\n')
                            .replace('\t', ' '))
            doc.page_content = cleaned_text
            yield doc
