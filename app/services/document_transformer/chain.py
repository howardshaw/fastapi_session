from typing import AsyncGenerator, List

from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from .base import DocumentTransformer

class ChainTransformer(DocumentTransformer):
    def __init__(self, transforms: List[DocumentTransformer], **kwargs):
        """
        将多个转换器串联在一起的转换器

        Args:
            transforms: 要串联的转换器列表
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.transforms = transforms

    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        current_docs = documents
        for transform in self.transforms:
            new_docs = []
            async_generator = await transform.transform(current_docs)
            async for doc in async_generator:
                new_docs.append(doc)
            current_docs = new_docs
        for doc in current_docs:
            yield doc