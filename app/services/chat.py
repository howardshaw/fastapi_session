from typing import AsyncGenerator, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from app.domain.chat import ChatMessage, MessageRole
from app.services.llm.base import LLMService


class ChatService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def _format_messages(self, messages: List[ChatMessage]) -> List[BaseMessage]:
        """将领域消息格式转换为LangChain消息格式"""
        formatted_messages = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                formatted_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                formatted_messages.append(AIMessage(content=msg.content))
        return formatted_messages

    async def chat_stream(
            self,
            messages: List[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """流式聊天"""
        formatted_messages = self._format_messages(messages)
        async for chunk in self.llm_service.generate_response_stream(formatted_messages):
            yield chunk
