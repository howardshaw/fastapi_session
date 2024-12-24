from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from .base import BaseRepository


class AccountRepository(BaseRepository):
    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        self._session_or_factory = session_or_factory
        super().__init__(session_or_factory, Account)
