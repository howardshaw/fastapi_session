from typing import Optional

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
