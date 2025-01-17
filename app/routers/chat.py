from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.containers import Container
from app.domain.chat import ChatMessage, MessageRole
from app.schemas.chat import ChatRequest
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
@inject
async def chat_stream(
        request: ChatRequest,
        chat_service: ChatService = Depends(Provide[Container.services.chat_service])
):
    """流式聊天接口"""

    # 将 schema 转换为领域模型
    domain_messages = [
        ChatMessage(
            role=MessageRole(msg.role),
            content=msg.content
        )
        for msg in request.messages
    ]

    async def stream_response():
        async for chunk in chat_service.chat_stream(domain_messages):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream"
    )
