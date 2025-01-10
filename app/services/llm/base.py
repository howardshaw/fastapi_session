from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Any, Dict

from langchain_core.runnables import run_in_executor


class FinishReason:
    MAX_TOKENS = "MAX_TOKENS"
    STOP = "STOP"
    OTHER = "OTHER"


@dataclass
class LLMResult:
    content: str
    finish_reason: FinishReason
    metadata: Dict[str, Any]


class LLMService(ABC):
    @property
    def _llm_type(self) -> str:
        return "custom"

    @abstractmethod
    def with_system_prompt(self, system_prompt: str) -> "LLMService":
        pass

    @abstractmethod
    def send_message(self, message: str, **kwargs: Any, ) -> LLMResult:
        pass

    async def asend_message(self, message: str, **kwargs: Any, ) -> LLMResult:
        return await run_in_executor(None, self.send_message, message, **kwargs)
