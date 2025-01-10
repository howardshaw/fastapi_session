from typing import Optional, Any, List
from langchain.schema import BaseMessage, ChatResult
from langchain_community.chat_models import ChatOllama

from app.settings import LLMSettings
from .base import LLMService, LLMResult
from app.logger import get_logger

logger = get_logger(__name__)

class OllamaService(LLMService):
    def __init__(self, settings: LLMSettings):
        self._llm = ChatOllama(
            base_url=settings.OLLAMA_HOST,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        self._system_prompt = settings.SYSTEM_PROMPT

    @property
    def _llm_type(self) -> str:
        return "ollama"

    def with_system_prompt(self, system_prompt: str) -> "LLMService":
        self._system_prompt = system_prompt
        return self

    def send_message(self, message: str, **kwargs: Any, ) -> LLMResult:
        if self._system_prompt:
            messages = [
                (
                    "system", self._system_prompt,
                ),
                ("human", message),
            ]
        else:
            messages = [("human", message)]
        response = self._llm.invoke(messages, **kwargs)
        logger.info(f"send_message response:{response}")
        return LLMResult(
            content=response.content.strip(),
        )

