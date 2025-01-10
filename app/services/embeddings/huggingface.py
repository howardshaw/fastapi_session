from langchain_huggingface import HuggingFaceEmbeddings

from app.settings import EmbeddingSettings
from .base import EmbeddingService


class HuggingFaceEmbeddingService(EmbeddingService):
    """HuggingFace Embedding服务"""

    def __init__(
            self,
            settings: EmbeddingSettings,
    ):
        self._model_name = settings.HUGGINGFACE_MODEL
        self._embeddings = HuggingFaceEmbeddings(
            model_name=settings.HUGGINGFACE_MODEL,
        )

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)
