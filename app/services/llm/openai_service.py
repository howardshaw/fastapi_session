from typing import Any

from langchain_openai import ChatOpenAI

from app.logger import get_logger
from app.settings import LLMSettings
from .base import LLMService, LLMResult, FinishReason

logger = get_logger(__name__)


class OpenAIService(LLMService):
    def __init__(self, settings: LLMSettings):
        logger.info(f"OpenAIService init called. {settings.OPENAI_BASE_URL} {settings.OPENAI_MODEL}")
        self._llm = ChatOpenAI(
            openai_api_base=settings.OPENAI_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            streaming=True
        )
        self._system_prompt = settings.SYSTEM_PROMPT

    @property
    def _llm_type(self) -> str:
        return "openai"

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
            finish_reason=FinishReason.STOP,
            metadata={},
        )
