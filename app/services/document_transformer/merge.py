from typing import AsyncGenerator, List

from langchain_core.documents import Document

from .base import DocumentTransformer


class MergeDocumentsTransformer(DocumentTransformer):
    def __init__(self, max_length: int = 4000, **kwargs):
        """
        合并相邻文档的转换器

        Args:
            max_length: 合并后文档的最大长度
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.max_length = max_length

    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        current_doc = None

        for doc in documents:
            if current_doc is None:
                current_doc = doc
                continue

            if len(current_doc.page_content) + len(doc.page_content) <= self.max_length:
                current_doc = Document(
                    page_content=current_doc.page_content + "\n" + doc.page_content,
                    metadata={
                        **current_doc.metadata,
                        "merged_docs": current_doc.metadata.get("merged_docs", 1) + 1
                    }
                )
            else:
                yield current_doc
                current_doc = doc

        if current_doc is not None:
            yield current_doc
