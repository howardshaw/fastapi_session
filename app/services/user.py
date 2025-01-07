import uuid
from typing import Optional

from app.core.database import Database
from app.logger import get_logger
from app.models import User
from app.models.account import Account
from app.repositories import UserRepository
from app.repositories.account import AccountRepository
from app.schemas.user import UserCreate
from app.utils.hash import hash_password

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: Database, user_repository: UserRepository, account_repository: AccountRepository):
        self.db = db
        self.user_repository = user_repository
        self.account_repository = account_repository

    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户和关联账户
        使用事务确保原子性
        """
        async with self.db.transaction():
            hashed_password = hash_password(user_data.password)
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["hashed_password"] = hashed_password

            user = await self.user_repository.create_user(User(**user_dict))

            logger.info(f"create user with id: {user.id}")
            account = Account(user_id=user.id, balance=100.0)
            await self.account_repository.create(account)
            return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱查询用户
        只读操作，使用普通session
        """
        return await self.user_repository.get_by_email(email)

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        通过ID查询用户
        只读操作，使用普通session
        """

        return await self.user_repository.get_user_by_id(user_id)
