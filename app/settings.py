import logging
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent


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


class VectorStoreSettings(BaseSettings):
    PROVIDER: str = "opensearch"  # chroma, milvus, opensearch
    COLLECTION_NAME: str = "vector"

    # Chroma settings
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Milvus settings
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""

    # OpenSearch settings
    OPENSEARCH_HOSTS: List[str] = ["localhost:9200"]
    OPENSEARCH_USER: Optional[str] = None
    OPENSEARCH_PASSWORD: Optional[str] = None
    OPENSEARCH_USE_SSL: bool = False
    OPENSEARCH_VERIFY_CERTS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VECTOR_STORE__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class DocumentStoreSettings(BaseSettings):
    PROVIDER: str = "mysql"  # mysql

    # mysql settings
    NAMESPACE: str = "doc_store"
    USER: str = ""
    PASSWORD: str = ""
    HOST: str = "127.0.0.1"
    PORT: str = "3306"
    ENGINE: str = ""
    DATABASE: str = ""
    URL: Optional[str] = None
    ASYNC_MODE: bool = False

    @field_validator("URL", mode="before")
    def assemble_db_connection(cls, v: str, info: ValidationInfo):
        if v is None:

            db_engine = info.data.get('ENGINE', '').lower()
            db_user = info.data.get('USER', '')
            db_password = info.data.get('PASSWORD', '')
            db_host = info.data.get('HOST', '')
            db_port = info.data.get('PORT', '')
            db_database = info.data.get('DATABASE', '')
            async_mode = info.data.get('ASYNC_MODE', False)

            if not all([db_engine, db_user, db_host, db_port, db_database]):
                print("Warning: Some database configuration values are missing")
            if async_mode:
                if db_engine == "mysql":
                    return f"mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset=utf8mb4"
                elif db_engine == "postgresql":
                    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
                elif db_engine == "sqlite":
                    return f"sqlite+aiosqlite:///{db_database}"
                else:
                    raise ValueError(
                        f"Unsupported DB_ENGINE:{db_engine}. Choose from 'mysql', 'postgresql', or 'sqlite'.")
            else:
                if db_engine == "mysql":
                    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset=utf8mb4"
                elif db_engine == "postgresql":
                    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
                elif db_engine == "sqlite":
                    return f"sqlite:///{db_database}"
                else:
                    raise ValueError(
                        f"Unsupported DB_ENGINE:{db_engine}. Choose from 'mysql', 'postgresql', or 'sqlite'.")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DOCUMENT_STORE__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


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


class LLMSettings(BaseSettings):
    PROVIDER: str = "openai"  # openai, ollama, claude
    SYSTEM_PROMPT: Optional[str] = None
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    # Ollama settings
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_TIMEOUT: int = 120

    # Claude settings
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    CLAUDE_MODEL: str = "claude-3-opus-20240229"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LLM__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class LogSettings(BaseSettings):
    LEVEL: str = "INFO"
    FORMAT: str = "JSON"
    COLORS: bool = True
    FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 默认10MB
    FILE_BACKUP_COUNT: int = 5  # 默认保留5个备份
    FILE_PATH: str = "logs/app.log"  # 默认日志文件路径

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOG__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class APISettings(BaseSettings):
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    METRICS_CONSOLE: bool = False
    INCLUDE_TRACE_ID: bool = True
    SHOW_TRACEBACKS: bool = True
    TRACEBACK_SHOW_LOCALS: bool = True
    TRACEBACK_MAX_FRAMES: int = 10
    CORS_ORIGINS: List[str] = ["*"]
    SERVICE_NAME: str = "api-server"
    ENVIRONMENT: str = "development"
    COMPRESSION: str = "gzip"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="API__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class SecuritySettings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COOKIE_SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SECURITY__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class TemporalSettings(BaseSettings):
    HOST: str = "localhost:7233"
    TRANSFER_QUEUE: str = "transfer-task-queue"
    TRANSLATE_QUEUE: str = "translate-task-queue"
    DSL_QUEUE: str = "dsl-task-queue"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TEMPORAL__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class OTLPSettings(BaseSettings):
    ENDPOINT: str = "http://localhost:4317"
    INSECURE: bool = True
    EXPORT_INTERVAL_MILLIS: int = 5000
    EXPORT_TIMEOUT_MILLIS: int = 10000
    MAX_QUEUE_SIZE: int = 2048
    MAX_EXPORT_BATCH_SIZE: int = 512
    SCHEDULE_DELAY_MILLIS: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OTLP__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class MinioSettings(BaseSettings):
    ENDPOINT: str = "localhost:9000"
    ACCESS_KEY: str = "minio-access-key"
    SECRET_KEY: str = "minio-secret-key"
    BUCKET: str = "resources"
    SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MINIO__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class DatabaseSettings(BaseSettings):
    USER: str = ""
    PASSWORD: str = ""
    HOST: str = "127.0.0.1"
    PORT: str = "3306"
    ENGINE: str = ""
    DATABASE: str = ""
    URL: Optional[str] = None

    @field_validator("URL", mode="before")
    def assemble_db_connection(cls, v: str, info: ValidationInfo):
        if v is None:

            db_engine = info.data.get('ENGINE', '')  # 使用 get 方法避免 KeyError
            db_user = info.data.get('USER', '')
            db_password = info.data.get('PASSWORD', '')
            db_host = info.data.get('HOST', '')
            db_port = info.data.get('PORT', '')
            db_database = info.data.get('DATABASE', '')

            if not all([db_engine, db_user, db_host, db_port, db_database]):
                print("Warning: Some database configuration values are missing")

            if db_engine == "mysql":
                return f"mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}?charset=utf8mb4"
            elif db_engine == "postgresql":
                return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
            elif db_engine == "sqlite":
                return f"sqlite+aiosqlite:///{db_database}"
            else:
                raise ValueError(f"Unsupported DB_ENGINE:{db_engine}. Choose from 'mysql', 'postgresql', or 'sqlite'.")
        return v

    def get_sync_url(self):
        """返回同步的数据库 URI，供 Alembic 使用"""
        if self.ENGINE == "mysql":
            return f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DATABASE}?charset=utf8mb4"
        elif self.ENGINE == "postgresql":
            return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DATABASE}"
        elif self.ENGINE == "sqlite":
            return f"sqlite:///{self.DATABASE}"
        return self.URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DATABASE__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )


class Settings(BaseSettings):
    PROJECT_NAME: str = "Langchain Temporal Service"
    REDIS_URL: str = "redis://localhost:6379"

    # 子模块设置
    API: APISettings = APISettings()
    LOG: LogSettings = LogSettings()
    SECURITY: SecuritySettings = SecuritySettings()
    TEMPORAL: TemporalSettings = TemporalSettings()
    OTLP: OTLPSettings = OTLPSettings()
    MINIO: MinioSettings = MinioSettings()
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
