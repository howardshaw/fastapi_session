import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from .api import APISettings
from .base import BaseAppSettings
from .database import DatabaseSettings
from .document_store import DocumentStoreSettings
from .embedding import EmbeddingSettings
from .llm import LLMSettings
from .log import LogSettings
from .observability import OTLPSettings
from .security import SecuritySettings
from .storage import StorageSettings
from .temporal import TemporalSettings
from .vector_store import VectorStoreSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


@lru_cache
def get_env_path() -> Path | None:
    import importlib

    try:
        importlib.import_module("dotenv")
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            logger.info(f"Loading environment from: {env_path}")
            return env_path
        else:
            logger.warning(f"Environment file not found at: {env_path}")
            return None
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
        return None


class Settings(BaseAppSettings):
    API: APISettings = APISettings()
    LOG: LogSettings = LogSettings()
    SECURITY: SecuritySettings = SecuritySettings()
    TEMPORAL: TemporalSettings = TemporalSettings()
    OTLP: OTLPSettings = OTLPSettings()
    STORAGE: StorageSettings = StorageSettings()
    DATABASE: DatabaseSettings = DatabaseSettings()
    VECTOR_STORE: VectorStoreSettings = VectorStoreSettings()
    DOCUMENT_STORE: DocumentStoreSettings = DocumentStoreSettings()
    EMBEDDING: EmbeddingSettings = EmbeddingSettings()
    LLM: LLMSettings = LLMSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


@lru_cache()
def get_settings() -> Settings:
    env_path = get_env_path()
    print(f"env path: {env_path}")
    if env_path:
        logger.info(f"Using environment file: {env_path}")
        settings = Settings(_env_file=env_path)
    else:
        logger.warning("No environment file found, using environment variables only")
        settings = Settings()

    # 打印关键配置信息
    logger.info("Settings loaded with:")
    logger.info(f"Environment file: {env_path or 'Not found'}")
    logger.info(f"Database URL: {settings.DATABASE.URL}")
    logger.info(f"Database Engine: {settings.DATABASE.ENGINE}")

    return settings


# 创建全局设置实例
settings = get_settings()
