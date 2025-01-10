from dataclasses import dataclass
from enum import Enum
from typing import List

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class ChatMessage:
    role: MessageRole
    content: str

@dataclass
class ChatConversation:
    messages: List[ChatMessage] 