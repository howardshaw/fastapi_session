import logging
from typing import Optional, Callable

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import OrderCreationError
from app.models import User, Account, Order
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository:
    def __init__(
            self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        self._session_or_factory = session_or_factory

    @property
    def session(self) -> AsyncSession:
        if isinstance(self._session_or_factory, AsyncSession):
            return self._session_or_factory
        return self._session_or_factory()

    async def create_user_with_account(self, user_data: UserCreate) -> User:
        """创建用户和关联账户"""
        # Hash the password
        hashed_password = pwd_context.hash(user_data.password)

        # Create new user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        self.session.add(db_user)
        await self.session.flush()
        await self.session.refresh(db_user)

        # Create associated account
        db_account = Account(
            user=db_user,
            balance=10.0
        )
        self.session.add(db_account)
        await self.session.flush()

        return db_user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        logger.info(f"get_user_by_id: {user_id} {self.session}")
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, username: str) -> User:
        """创建用户（简单版本，用于测试）"""
        logger.info(f"create_user: {username} {self.session}")
        user = User(username=username)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user


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
