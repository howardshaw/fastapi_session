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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        logger.info(f"Initializing unit of work. {session}")
        self._session = session

    @asynccontextmanager
    async def transaction(self):
        """
        Provide a transactional scope around a series of operations.
        """
        logger.info(f"Starting transaction with session: {id(self._session)}")
        try:
            yield
            logger.info(f"Committing transaction with session: {id(self._session)}")
            await self._session.commit()
            logger.info(f"Transaction committed with session: {id(self._session)}")
        except (OrderCreationError, InsufficientFundsError, AccountNotFoundError, TransferError) as e:
            # Business exceptions - rollback and propagate
            logger.error(f"Business error in transaction with session {id(self._session)}: {type(e).__name__} - {str(e)}")
            await self._session.rollback()
            raise
        except SQLAlchemyError as e:
            # Database errors - rollback and wrap
            logger.error(f"Database error in transaction with session {id(self._session)}: {type(e).__name__} - {str(e)}")
            await self._session.rollback()
            raise DatabaseError(f"Database operation failed: {str(e)}")
        except Exception as e:
            # Other errors - rollback and propagate
            logger.error(f"Unexpected error in transaction with session {id(self._session)}: {type(e).__name__} - {str(e)}")
            await self._session.rollback()
            raise
