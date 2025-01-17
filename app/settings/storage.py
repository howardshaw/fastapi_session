from pydantic_settings import BaseSettings, SettingsConfigDict
class StorageSettings(BaseSettings):
    PROVIDER: str = "minio"  # openai, ollama, claude

    # MINIO settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio-access-key"
    MINIO_SECRET_KEY: str = "minio-secret-key"
    MINIO_BUCKET: str = "resources"
    MINIO_SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STORAGE__",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="allow",
    )