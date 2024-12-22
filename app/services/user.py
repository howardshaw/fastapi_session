from typing import Optional

from app.core.database import Database
from app.logger import get_logger
from app.models import User
from app.repositories import UserRepository
from app.schemas.user import UserCreate

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: Database, user_repository: UserRepository):
        self.db = db
        self.user_repository = user_repository

    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户和关联账户
        使用事务确保原子性
        """
        async with self.db.transaction():
            return await self.user_repository.create_user_with_account(user_data)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱查询用户
        只读操作，使用普通session
        """
        return await self.user_repository.get_user_by_email(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        通过ID查询用户
        只读操作，使用普通session
        """

        return await self.user_repository.get_user_by_id(user_id)
