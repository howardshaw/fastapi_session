from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


@lru_cache
def get_env_path() -> Path | None:
    import importlib

    try:
        importlib.import_module("dotenv")
    except ImportError:
        return
    if Path.exists(BASE_DIR / ".env"):
        return BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Langchain Tempral Service"
    # FastAPI 配置
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["*"]

    TEMPORAL_HOST: str = "localhost:7233"
    REDIS_URL: str = "redis://localhost:6379"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai-hk.com/v1"
    OPENAI_MODEL: str = ""

    TEMPORAL_TRANSFER_QUEUE: str = "transfer-task-queue"
    TEMPORAL_TRANSLATE_QUEUE: str = "translate-task-queue"

    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    class Config:
        # env_file = ".env"
        extra = "allow"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings(_env_file=get_env_path())


# 创建全局设置实例
settings = get_settings()
