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
    LOG_FORMAT: str = "JSON"
    LOG_COLORS: bool = True
    METRICS_CONSOLE: bool = False
    INCLUDE_TRACE_ID: bool = True
    SHOW_TRACEBACKS: bool = True
    TRACEBACK_SHOW_LOCALS: bool = True
    TRACEBACK_MAX_FRAMES: int = 10
    CORS_ORIGINS: List[str] = ["*"]
    API_SERVICE_NAME: str = "api-server"
    ENVIRONMENT: str = "development"
    COMPRESSION: str = "gzip"

    TEMPORAL_HOST: str = "localhost:7233"
    OTLP_ENDPOINT: str = "http://localhost:4317"
    OTLP_INSECURE: bool = True
    EXPORT_INTERVAL_MILLIS: int = 5000
    EXPORT_TIMEOUT_MILLIS: int = 10000
    MAX_QUEUE_SIZE: int = 2048
    MAX_EXPORT_BATCH_SIZE: int = 512
    SCHEDULE_DELAY_MILLIS: int = 5000

    REDIS_URL: str = "redis://localhost:6379"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai-hk.com/v1"
    OPENAI_MODEL: str = ""

    TEMPORAL_TRANSFER_QUEUE: str = "transfer-task-queue"
    TEMPORAL_TRANSLATE_QUEUE: str = "translate-task-queue"
    TEMPORAL_DSL_QUEUE: str = "dsl-task-queue"

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
