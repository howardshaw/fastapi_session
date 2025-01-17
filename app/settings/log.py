from pydantic_settings import BaseSettings, SettingsConfigDict


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
