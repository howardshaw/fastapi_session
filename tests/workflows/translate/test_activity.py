import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from langchain_core.messages import AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk, ChatResult

from app.workflows.translate.activities import TranslateActivities, TranslateParams


class AsyncIterator:
    """异步迭代器辅助类"""
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)


@pytest.mark.asyncio
async def test_translate_phrase_success():
    """测试翻译短语成功的场景"""
    # Mock dependencies
    mock_llm = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0  # 模拟 Redis exists 返回 0，表示 key 不存在
    mock_queue_manager = AsyncMock()
    mock_queue_manager.is_cancelled.return_value = False

    # Set up mock behavior
    chunks = [
        AIMessageChunk(content="Hello"),
        AIMessageChunk(content=" World!")
    ]
    mock_chain = MagicMock()
    mock_chain.astream.return_value = AsyncIterator(chunks)
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    with patch("app.workflows.translate.activities.ChatPromptTemplate.from_messages", return_value=mock_prompt), \
         patch("app.core.queue_manager.QueueManager", return_value=mock_queue_manager):
        # Instantiate the class
        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        # Define test inputs
        params = TranslateParams(phrase="Hola", language="English")
        task_id = "test_task_123"
        # async for chunk in mock_chain.astream({"phrase": params.phrase, "language": params.language}):
        #     if isinstance(chunk, AIMessageChunk):
        #         print(f"Publishing chunk: {chunk.content}")  # 添加调试信息
        #         await mock_queue_manager.publish({
        #             "content": chunk.content
        #         })
        #
        #     else:
        #         print(f"Chunk is not AIMessageChunk: {chunk}, {type(chunk)}")

        # Call the method
        result = await activities.translate_phrase(params, task_id)


        # Assertions
        assert result == "Hello World!"
        assert mock_queue_manager.publish.await_count == 2
        mock_queue_manager.publish.assert_has_awaits([
            call({"content": "Hello"}),
            call({"content": " World!"})
        ])
        print(mock_queue_manager.publish.await_args_list)


@pytest.mark.asyncio
async def test_translate_phrase_llm_error():
    """测试 LLM 调用失败的场景"""
    # Mock dependencies
    mock_llm = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0  # 模拟 Redis exists 返回 0，表示 key 不存在
    mock_queue_manager = AsyncMock()
    mock_queue_manager.is_cancelled.return_value = False

    # Set up mock behavior to simulate LLM error
    mock_chain = MagicMock()
    mock_chain.astream.side_effect = Exception("LLM error")
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    with patch("app.workflows.translate.activities.ChatPromptTemplate.from_messages", return_value=mock_prompt), \
         patch("app.core.queue_manager.QueueManager", return_value=mock_queue_manager):
        # Instantiate the class
        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        # Define test inputs
        params = TranslateParams(phrase="Hola", language="English")
        task_id = "test_task_123"

        # Call the method and expect exception
        with pytest.raises(Exception) as exc_info:
            await activities.translate_phrase(params, task_id)
        assert str(exc_info.value) == "LLM error"

        # Verify no messages were published
        mock_queue_manager.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_translate_phrase_redis_error():
    """测试 Redis 操作失败的场景"""
    # Mock dependencies
    mock_llm = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0  # 模拟 Redis exists 返回 0，表示 key 不存在
    mock_queue_manager = AsyncMock()
    mock_queue_manager.is_cancelled.return_value = False

    # Set up mock behavior
    chunks = [AIMessageChunk(content="Hello")]
    mock_chain = MagicMock()
    mock_chain.astream.return_value = AsyncIterator(chunks)
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    # Simulate Redis error
    mock_queue_manager.publish.side_effect = Exception("Redis error")

    with patch("app.workflows.translate.activities.ChatPromptTemplate.from_messages", return_value=mock_prompt), \
         patch("app.core.queue_manager.QueueManager", return_value=mock_queue_manager):
        # Instantiate the class
        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        # Define test inputs
        params = TranslateParams(phrase="Hola", language="English")
        task_id = "test_task_123"

        # Call the method and expect exception
        with pytest.raises(Exception) as exc_info:
            await activities.translate_phrase(params, task_id)
        assert str(exc_info.value) == "Redis error"

        # Verify publish was attempted
        mock_queue_manager.publish.assert_awaited_once_with({"content": "Hello"})


@pytest.mark.asyncio
async def test_translate_phrase_empty_input():
    """测试空输入的场景"""
    # Mock dependencies
    mock_llm = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0  # 模拟 Redis exists 返回 0，表示 key 不存在
    mock_queue_manager = AsyncMock()
    mock_queue_manager.is_cancelled.return_value = False

    # Set up mock behavior for empty input
    chunks = [AIMessageChunk(content="")]
    mock_chain = MagicMock()
    mock_chain.astream.return_value = AsyncIterator(chunks)
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    with patch("app.workflows.translate.activities.ChatPromptTemplate.from_messages", return_value=mock_prompt), \
         patch("app.core.queue_manager.QueueManager", return_value=mock_queue_manager):
        # Instantiate the class
        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        # Define test inputs
        params = TranslateParams(phrase="", language="English")
        task_id = "test_task_123"

        # Call the method
        result = await activities.translate_phrase(params, task_id)

        # Assertions
        assert result == ""
        mock_queue_manager.publish.assert_awaited_once_with({"content": ""})


@pytest.mark.asyncio
async def test_complete_translate():
    """测试完成翻译的场景"""
    # Mock dependencies
    mock_llm = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0  # 模拟 Redis exists 返回 0，表示 key 不存在
    mock_queue_manager = AsyncMock()
    mock_queue_manager.is_cancelled.return_value = False

    with patch("app.workflows.translate.activities.ChatPromptTemplate.from_messages"), \
         patch("app.core.queue_manager.QueueManager", return_value=mock_queue_manager):
        # Instantiate the class
        activities = TranslateActivities(llm=mock_llm, redis_client=mock_redis)

        # Define test input
        task_id = "test_task_123"

        # Call the method
        await activities.complete_translate(task_id)

        # Verify mark_complete was called
        mock_queue_manager.mark_complete.assert_awaited_once()