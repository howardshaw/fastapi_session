from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.exceptions import DatabaseError, OrderCreationError


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self._session = session

    @asynccontextmanager
    async def transaction(self):
        try:
            yield
            await self._session.commit()
        except OrderCreationError:
            await self._session.rollback()
            raise
        except Exception as e:
            await self._session.rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")