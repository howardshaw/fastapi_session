from pydantic_settings import BaseSettings, SettingsConfigDict


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
