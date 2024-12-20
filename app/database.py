import asyncio
import functools
import logging
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from typing import AsyncGenerator
from typing import Callable, Awaitable, Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_task = ContextVar("current_task")
session_context: ContextVar[str] = ContextVar("session_context")


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)


AsyncCallable = Callable[..., Awaitable]


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(
            db_url,
            echo=True,
            poolclass=AsyncAdaptedQueuePool,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
        )
        async_session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        self._session_factory = async_scoped_session(
            async_session_factory, scopefunc=asyncio.current_task,
        )

    def get_session(self) -> AsyncSession:
        return self._session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for read-only operations.
        Does not start a transaction, suitable for queries.
        """
        session: AsyncSession = self._session_factory()
        logger.info(f"Created read session: {id(session)}")
        try:
            yield session
        finally:
            await session.close()
            logger.info(f"Closed read session: {id(session)}")

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for transactional operations.
        Automatically handles commit/rollback.
        """
        session: AsyncSession = self._session_factory()
        logger.debug(f"Created transaction session: {id(session)}")

        try:
            # 开始事务
            if not session.in_transaction():
                await session.begin()
            logger.debug(f"Started transaction: {id(session)}")

            try:
                yield session
                # 如果没有异常，提交事务
                await session.commit()
                logger.debug(f"Committed transaction: {id(session)}")
            except Exception as e:
                # 如果有异常，回滚事务
                await session.rollback()
                logger.error(f"Rolled back transaction {id(session)}: {str(e)}")
                raise
        finally:
            # 确保session总是被关闭
            await session.close()
            logger.debug(f"Closed transaction session: {id(session)}")

    async def init_db(self) -> None:
        """Initialize database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")

    def transactional(self, func: AsyncCallable) -> AsyncCallable:
        """
        装饰器：为函数提供事务上下文
        自动处理事务的开始、提交和回滚
        """

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with self.transaction() as session:
                # 将 session 注入到 kwargs 中
                kwargs['session'] = session
                return await func(*args, **kwargs)

        return wrapper
