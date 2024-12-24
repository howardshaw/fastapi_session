from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import ValidationInfo, field_validator
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
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 默认10MB
    LOG_FILE_BACKUP_COUNT: int = 5  # 默认保留5个备份
    LOG_FILE_PATH: str = "logs/app.log"  # 默认日志文件路径
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

    # DATABASE
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = "127.0.0.1"
    DB_PORT: str = "3306"
    DB_ENGINE: str = ""
    DB_DATABASE: str = ""
    DATABASE_URL: str = None

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(  # pylint: disable=no-self-argument
            cls, v: str, info: ValidationInfo
    ):
        if v is None:
            db_engine = info.data['DB_ENGINE']
            db_user = info.data['DB_USER']
            db_password = info.data['DB_PASSWORD']
            db_host = info.data['DB_HOST']
            db_port = info.data['DB_PORT']
            db_database = info.data['DB_DATABASE']

            if db_engine == "mysql":
                return f"mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset=utf8mb4"
            elif db_engine == "postgresql":
                return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
            elif db_engine == "sqlite":
                return f"sqlite+aiosqlite:///{db_database}"
            else:
                raise ValueError("Unsupported DB_ENGINE. Choose from 'mysql', 'postgresql', or 'sqlite'.")
        return v

    def get_sync_database_url(self):
        """返回同步的数据库 URI，供 Alembic 使用"""
        db_engine = self.DB_ENGINE
        db_user = self.DB_USER
        db_password = self.DB_PASSWORD
        db_host = self.DB_HOST
        db_port = self.DB_PORT
        db_database = self.DB_DATABASE

        if db_engine == "mysql":
            return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset=utf8mb4"
        elif db_engine == "postgresql":
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
        elif db_engine == "sqlite":
            return f"sqlite:///{db_database}"
        else:
            # 对于其他数据库，直接返回异步版本
            return self.DATABASE_URL

    class Config:
        # env_file = ".env"
        extra = "allow"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings(_env_file=get_env_path())


# 创建全局设置实例
settings = get_settings()
