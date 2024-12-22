from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderCreationError
from app.logger import get_logger
from app.models import Order

logger = get_logger(__name__)


class OrderRepository:
    def __init__(
            self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        self._session_or_factory = session_or_factory

    @property
    def session(self) -> AsyncSession:
        if isinstance(self._session_or_factory, AsyncSession):
            return self._session_or_factory
        return self._session_or_factory()

    async def create_order(
            self,
            user_id: int,
            description: str,
            amount: float,
    ) -> Order:
        logger.info(f"create order with {self.session} {type(self.session)}")
        if description == "First order":
            raise OrderCreationError("Cannot create order with description 'First order'")

        order = Order(
            user_id=user_id,
            description=description,
            amount=amount
        )

        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order
