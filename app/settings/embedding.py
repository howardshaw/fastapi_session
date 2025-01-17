from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingSettings(BaseSettings):
    PROVIDER: str = "openai"  # openai, huggingface

    # OpenAI settings
    OPENAI_MODEL: str = "text-embedding-ada-002"
    OPENAI_API_BASE: str = "http://api.openai.com/v1/"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_DIMENSION: int = 1536

    # HuggingFace settings
    HUGGINGFACE_MODEL: str = "all-MiniLM-L6-v2"
    HUGGINGFACE_DEVICE: str = "cpu"

    # Ollama settings
    OLLAMA_MODEL: str = "bge-m3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EMBEDDING__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )
