from typing import Any

from langchain_anthropic import ChatAnthropic

from app.logger import get_logger
from app.settings import LLMSettings
from .base import LLMService, LLMResult

logger = get_logger(__name__)


class ClaudeService(LLMService):
    def __init__(self, settings: LLMSettings):
        self._llm = ChatAnthropic(
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            anthropic_api_url=settings.ANTHROPIC_BASE_URL,
            model=settings.CLAUDE_MODEL
        )
        self._system_prompt = settings.SYSTEM_PROMPT

    @property
    def _llm_type(self) -> str:
        return "claude"

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
