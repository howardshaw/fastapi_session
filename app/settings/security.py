from pydantic_settings import BaseSettings, SettingsConfigDict


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
