import logging
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    DatabaseError,
    OrderCreationError,
    InsufficientFundsError,
    AccountNotFoundError,
    TransferError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session

    @asynccontextmanager
    async def transaction(self):
        try:
            yield
            await self._session.commit()
        except (OrderCreationError, InsufficientFundsError, AccountNotFoundError, TransferError) as e:
            # 业务异常，回滚并直接向上传播
            logger.error(f"Transaction failed: {type(e)} {e}")
            await self._session.rollback()
            raise
        except SQLAlchemyError as e:
            # 数据库异常，包装成 DatabaseError
            await self._session.rollback()
            raise DatabaseError(f"Database operation failed: {str(e)}")
        except Exception:
            # 其他未知异常，回滚但不包装
            await self._session.rollback()
            raise
