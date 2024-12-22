from dataclasses import dataclass

import redis.asyncio as redis
from langchain.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from temporalio import activity

from app.core.queue_manager import QueueManager
from app.logger.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TranslateParams:
    phrase: str
    language: str


class TranslateActivities:
    def __init__(self, llm: BaseChatModel, redis_client: redis.Redis):
        self._llm = llm
        self._redis = redis_client

    @activity.defn
    async def translate_phrase(
            self,
            params: TranslateParams,
            task_id: str,
    ) -> str:
        queue_manager = QueueManager(redis_client=self._redis, task_id=task_id)
        template = """You are a helpful assistant who translates between languages.
            Translate the following phrase into the specified language: {phrase}
            Language: {language}"""
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", template),
                ("human", "Translate"),
            ]
        )
        chain = chat_prompt | self._llm
        ret = []
        async for chunk in chain.astream({"phrase": params.phrase, "language": params.language}):
            if isinstance(chunk, AIMessageChunk):
                await queue_manager.publish({
                    "content": chunk.content
                })
                ret.append(chunk.content)
            logger.info(f"published chunk: {chunk}, {type(chunk)}")
        logger.info(f"final ret: {ret}")
        return "".join(ret)

    @activity.defn
    async def complete_translate(self, task_id: str):
        queue_manager = QueueManager(redis_client=self._redis, task_id=task_id)
        await queue_manager.mark_complete()
