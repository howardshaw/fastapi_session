from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings
from langchain_core.runnables import run_in_executor


class EmbeddingService(ABC):

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        pass

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await run_in_executor(None, self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await run_in_executor(None, self.embed_query, text)

    @property
    def dimension(self) -> int:
        """返回向量维度"""

        # 不同模型有不同维度，可以通过embed一个样本文本来获取维度
        return len(self.embed_query("sample text"))


class LangChainedEmbeddingWrapper(Embeddings):

    def __init__(self, embedding: EmbeddingService):
        self.embedding = embedding

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embedding.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embedding.embed_query(text)
