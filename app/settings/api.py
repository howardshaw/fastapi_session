from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


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
