from langchain_openai import OpenAIEmbeddings

from app.settings import EmbeddingSettings
from .base import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(
            self,
            settings: EmbeddingSettings,
    ):
        self._embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_MODEL,
            openai_api_base=settings.OPENAI_API_BASE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self._model_name = settings.OPENAI_MODEL
        self._dimension = settings.OPENAI_DIMENSION

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    @property
    def dimension(self) -> int:
        return self._dimension  # OpenAI ada-002 model dimension

    @property
    def model_name(self) -> str:
        return self._model_name
