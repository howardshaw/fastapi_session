from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseAppSettings(BaseSettings):
    PROJECT_NAME: str = "Langchain Temporal Service"
    REDIS_URL: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    ) 