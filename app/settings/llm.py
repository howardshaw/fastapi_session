from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


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
