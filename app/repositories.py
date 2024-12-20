import logging
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import OrderCreationError
from app.models import User, Order

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(
            self, session_or_factory: AsyncSession | Callable[[], AsyncSession], ) -> None:
        self._session_or_factory = session_or_factory

    @property
    def session(self) -> AsyncSession:
        if isinstance(self._session_or_factory, AsyncSession):
            return self._session_or_factory
        return self._session_or_factory()

    async def create_user(self, name: str):
        logger.info(f"Creating user {name} with session {self.session}")
        new_user = User(username=name)
        self.session.add(new_user)
        await self.session.flush()
        await self.session.refresh(new_user)
        return new_user


class OrderRepository:
    # def __init__(self, session_factory: Callable[..., AbstractContextManager[AsyncSession]]):
    #     self._session_factory = session_factory

    def __init__(
            self, session_or_factory: AsyncSession | Callable[[], AsyncSession], ) -> None:
        self._session_or_factory = session_or_factory

    @property
    def session(self) -> AsyncSession:
        if isinstance(self._session_or_factory, AsyncSession):
            return self._session_or_factory
        return self._session_or_factory()

    async def create_order(self, user_id: int, description: str, amount: float):
        logger.info(f"create order with {self.session} {type(self.session)}")
        if description == "First order":
            raise OrderCreationError("Cannot create order with description 'First order'")
        new_order = Order(user_id=user_id, description=description, amount=amount)
        self.session.add(new_order)
        await self.session.flush()
        await self.session.refresh(new_order)
        return new_order
