from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Order
from app.exceptions import OrderCreationError


class UserRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_user(self, name: str):
        new_user = User(username=name)
        self._session.add(new_user)
        await self._session.flush()
        await self._session.refresh(new_user)
        return new_user


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_order(self, user_id: int, description: str,amount: float):
        print(f"RepositoryB {self._session} {type(self._session)}")
        if description == "First order":
            raise OrderCreationError("Cannot create order with description 'First order'")
        new_order = Order(user_id=user_id, description=description,amount=amount)
        self._session.add(new_order)
        await self._session.flush()
        await self._session.refresh(new_order)
        return new_order
