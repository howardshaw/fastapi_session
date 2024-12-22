import re
import uuid
from typing import Any, Iterator, List, Optional, cast
from temporalio.client import WorkflowFailureError
from unittest.mock import AsyncMock, MagicMock
import pytest
import redis.asyncio as redis
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.fake_chat_models import FakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from temporalio.exceptions import ApplicationError
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from app.workflows.translate.activities import TranslateActivities, TranslateParams
from app.workflows.translate.workflows import TranslateWorkflow


class CustomFakeChatModel(FakeChatModel):
    """自定义的 FakeChatModel，支持固定响应和错误模拟"""

    def __init__(self, response: str = "你好，我能帮你什么？", should_fail: bool = False):
        super().__init__()
        self._response = response
        self.should_fail = should_fail
        self.calls = []

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        """生成响应"""
        self.calls.append(messages)
        if self.should_fail:
            raise Exception("LLM error")
            
        message = AIMessage(content=self._response)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])


class MockRedis:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.data = {}
        self.rpush = AsyncMock()
        self.delete = AsyncMock()

    async def rpush(self, key: str, value: str) -> int:
        if self.should_fail:
            raise redis.RedisError("Redis connection error")
        await self.rpush(key, value)
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
        return len(self.data[key])

    async def delete(self, key: str) -> int:
        if self.should_fail:
            raise redis.RedisError("Redis connection error")
        await self.delete(key)
        return self.data.pop(key, None) is not None


@pytest.fixture
def task_queue_name():
    return str(uuid.uuid4())


@pytest.fixture
def task_id():
    return str(uuid.uuid4())


@pytest.mark.asyncio
async def test_successful_translation(task_queue_name, task_id) -> None:
    """测试成功的翻译场景"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        data = TranslateParams(
            "How can I help you?",
            "chinese"
        )

        # mock_llm = CustomFakeChatModel()
        # mock_redis = MockRedis()
        # Mock the dependencies
        mock_llm = AsyncMock()  # Mock BaseChatModel
        mock_redis = AsyncMock()  # Mock Redis client

        # Set up mock behavior
        mock_llm.ainvoke.return_value = "你好，我能帮你什么？"  # Mock LLM response
        mock_llm.invoke.return_value = "你好，我能帮你什么？"  # Mock LLM response
        mock_redis.set.return_value = True  # Simulate successful Redis storage

        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        async with Worker(
                env.client,
                task_queue=task_queue_name,
                workflows=[TranslateWorkflow],
                activities=[activities.translate_phrase, activities.complete_translate],
        ):
            result = await env.client.execute_workflow(
                TranslateWorkflow.run,
                args=[data, task_id],
                id=task_id,
                task_queue=task_queue_name,
            )

            assert result == "你好，我能帮你什么？"
            assert len(mock_llm.calls) == 1  # 确认 LLM 被调用了一次
            await mock_redis.rpush.assert_called()  # 确认 Redis rpush 被调用
            await mock_redis.delete.assert_called()  # 确认 Redis delete 被调用


@pytest.mark.asyncio
async def test_llm_error(task_queue_name, task_id) -> None:
    """测试 LLM 错误场景"""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        data = TranslateParams(
            "How can I help you?",
            "chinese"
        )

        # mock_llm = CustomFakeChatModel()
        # mock_redis = MockRedis()
        mock_llm = AsyncMock()  # Mock BaseChatModel
        mock_redis = AsyncMock()  # Mock Redis client

        # Set up mock behavior
        mock_llm.ainvoke.return_value = "你好，我能帮你什么？"
        mock_redis.set.return_value = True  # Simulate successful Redis storage

        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        async with Worker(
                env.client,
                task_queue=task_queue_name,
                workflows=[TranslateWorkflow],
                activities=[activities.translate_phrase, activities.complete_translate],
        ):
            with pytest.raises(ApplicationError):
                await env.client.execute_workflow(
                    TranslateWorkflow.run,
                    args=[data, task_id],
                    id=task_id,
                    task_queue=task_queue_name,
                )
