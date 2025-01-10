from langchain_ollama import OllamaEmbeddings

from app.settings import EmbeddingSettings
from .base import EmbeddingService


class OllamaEmbeddingService(EmbeddingService):
    """OpenAI Embedding服务"""

    def __init__(
            self,
            settings: EmbeddingSettings,
    ):
        self._embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        self._model_name = settings.OLLAMA_MODEL
        super().__init__(self._embeddings)

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)
