from pydantic_settings import BaseSettings, SettingsConfigDict

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