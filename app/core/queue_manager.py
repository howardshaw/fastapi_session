import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Any, Optional

import redis.asyncio as redis

from app.logger import logger


class QueueStatus(str, Enum):
    """Queue message status enumeration"""
    COMPLETE = "complete"
    EXIT = "exit"
    ERROR = "error"
    PROCESSING = "processing"
    CANCEL = "cancel"  # 用户主动终止状态


@dataclass
class QueueMessage:
    """Queue message data structure"""
    data: dict[str, Any]
    status: Optional[QueueStatus] = None

    @classmethod
    def from_json(cls, json_str: str) -> "QueueMessage":
        """Create QueueMessage from JSON string"""
        try:
            data = json.loads(json_str)
            status = QueueStatus(data.pop("status")) if "status" in data else None
            return cls(data=data, status=status)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            raise ValueError(f"Invalid JSON format: {e}") from e
        except ValueError as e:
            logger.error(f"Invalid status value: {e}")
            raise ValueError(f"Invalid status value: {e}") from e

    def to_json(self) -> str:
        """Convert QueueMessage to JSON string"""
        data = self.data.copy()
        if self.status:
            data["status"] = self.status.value
        return json.dumps(data)


class QueueError(Exception):
    """Base exception for queue operations"""
    pass


class QueueTimeoutError(QueueError):
    """Raised when queue operation times out"""
    pass


class QueueCancelledError(QueueError):
    """Raised when queue is cancelled by user"""
    pass


class QueueManager:
    """Redis-based queue manager for handling task messages"""

    def __init__(
            self,
            redis_client: redis.Redis,
            task_id: str | None = None,
    ):
        """
        Initialize QueueManager
        
        Args:
            redis_client: Redis client instance
            task_id: Optional task ID. If not provided, a new UUID will be generated
        """
        self._redis_client = redis_client
        self._task_id = task_id or str(uuid.uuid4())
        self._update_keys()

    def _update_keys(self) -> None:
        """Update Redis keys based on task_id"""
        self._queue_key = f"queue:{self._task_id}"
        self._cancel_key = f"cancel:{self._task_id}"

    @property
    def task_id(self) -> str:
        """Get the task ID"""
        return self._task_id

    @task_id.setter
    def task_id(self, value: str) -> None:
        """
        Set the task ID and update related keys
        
        Args:
            value: New task ID
        """
        self._task_id = value
        self._update_keys()

    async def publish(self, data: dict[str, Any]) -> None:
        """
        Publish data to the queue
        
        Args:
            data: Dictionary containing the message data
        
        Raises:
            QueueError: If publishing fails
            QueueCancelledError: If queue is cancelled
        """
        try:
            # 检查是否已取消
            if await self.is_cancelled():
                raise QueueCancelledError(f"Queue {self.task_id} has been cancelled")

            message = QueueMessage(data=data)
            await self._redis_client.rpush(self._queue_key, message.to_json())
            logger.debug(f"Published message to {self._queue_key}: {data}")
        except QueueCancelledError:
            raise
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise QueueError(f"Failed to publish message: {e}") from e

    async def mark_complete(self, expire_seconds: int = 3600) -> None:
        """
        Mark the queue as complete and set expiration
        
        Args:
            expire_seconds: Time in seconds after which the queue will be deleted
        
        Raises:
            QueueError: If marking complete fails
        """
        try:
            message = QueueMessage(data={}, status=QueueStatus.COMPLETE)
            await self._redis_client.rpush(self._queue_key, message.to_json())
            await self._redis_client.expire(self._queue_key, expire_seconds)
            # 同时删除取消标记
            await self._redis_client.delete(self._cancel_key)
            logger.debug(f"Marked {self._queue_key} as complete with {expire_seconds}s expiry")
        except Exception as e:
            logger.error(f"Failed to mark queue as complete: {e}")
            raise QueueError(f"Failed to mark queue as complete: {e}") from e

    async def cancel(self) -> None:
        """
        Cancel the queue processing
        
        Raises:
            QueueError: If cancellation fails
        """
        try:
            # 设置取消标记
            await self._redis_client.set(self._cancel_key, "1")
            # 发送取消消息
            message = QueueMessage(data={}, status=QueueStatus.CANCEL)
            await self._redis_client.rpush(self._queue_key, message.to_json())
            logger.info(f"Queue {self.task_id} has been cancelled")
        except Exception as e:
            logger.error(f"Failed to cancel queue: {e}")
            raise QueueError(f"Failed to cancel queue: {e}") from e

    async def is_cancelled(self) -> bool:
        """
        Check if the queue has been cancelled
        
        Returns:
            bool: True if cancelled, False otherwise
        """
        try:
            return bool(await self._redis_client.exists(self._cancel_key))
        except Exception as e:
            logger.error(f"Failed to check cancel status: {e}")
            return False

    async def listen(self, timeout: int = 30) -> AsyncGenerator[dict[str, Any], None]:
        """
        Listen for messages from the queue
        
        Args:
            timeout: Time in seconds to wait for new messages
        
        Yields:
            Dictionary containing message data
        
        Raises:
            QueueTimeoutError: If no message received within timeout
            QueueCancelledError: If queue is cancelled
            QueueError: If message processing fails
        """
        while True:
            try:
                # 检查是否已取消
                if await self.is_cancelled():
                    logger.info(f"Queue {self.task_id} processing cancelled")
                    raise QueueCancelledError(f"Queue {self.task_id} has been cancelled")

                result = await self._redis_client.blpop(self._queue_key, timeout=timeout)
                if not result:
                    logger.debug(f"Queue {self._queue_key} listen timeout after {timeout}s")
                    raise QueueTimeoutError(f"No message received within {timeout} seconds")

                message = QueueMessage.from_json(result[1])
                logger.debug(f"Received message from {self._queue_key}: {message.data}")

                if message.status in (QueueStatus.COMPLETE, QueueStatus.EXIT, QueueStatus.CANCEL):
                    logger.info(f"Queue {self._queue_key} finished with status: {message.status}")
                    if message.status == QueueStatus.CANCEL:
                        raise QueueCancelledError(f"Queue {self.task_id} was cancelled")
                    break

                yield message.data

            except QueueTimeoutError:
                break
            except QueueCancelledError:
                raise
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise QueueError(f"Failed to process message: {e}") from e

    async def clear(self) -> None:
        """
        Clear all messages from the queue and cancel status
        
        Raises:
            QueueError: If clearing fails
        """
        try:
            await self._redis_client.delete(self._queue_key, self._cancel_key)
            logger.debug(f"Cleared queue {self._queue_key} and cancel status")
        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            raise QueueError(f"Failed to clear queue: {e}") from e
