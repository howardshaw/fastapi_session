import uuid
from typing import Optional, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicatedError
from app.logger import get_logger
from app.models import User
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class UserRepository(BaseRepository):
    """用户仓储，处理用户相关的数据库操作"""

    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        super().__init__(session_or_factory, User)

    async def create_user(self, user: User) -> User:
        """创建用户和关联账户"""

        # 创建用户
        try:
            db_user = await self.create(user)

            return db_user
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise DuplicatedError(detail="Username or email already exists")

    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        stmt = select(self.model).filter(self.model.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, id: uuid.UUID) -> Optional[User]:
        """通过id获取用户"""
        return await self.read_by_id(id)

    async def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        stmt = select(self.model).filter(self.model.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
