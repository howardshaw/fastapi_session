from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Database
from app.core.exceptions import AccountNotFoundError, DatabaseError, InsufficientFundsError, AccountLockedError
from app.logger import get_logger
from app.models import Account

logger = get_logger(__name__)


class TransactionService:
    def __init__(self, db: Database):
        self.db = db

    @property
    def session(self) -> AsyncSession:
        return self.db.get_session()

    async def get_account_by_id(self, account_id: int) -> Account | None:
        """Get account by ID"""
        try:
            logger.info(f"get account by id: {account_id} {self.session}")
            result = await self.session.execute(
                select(Account).filter(Account.id == account_id)
            )
            account = result.scalar_one_or_none()
            if not account:
                raise AccountNotFoundError(account_id)
            return account
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting account: {str(e)}")
            raise DatabaseError(f"Failed to get account {account_id}")

    async def get_account_by_user_id(self, user_id: int):
        """Read-only operation to get account by user ID"""
        query = select(Account).where(Account.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _withdraw(self, account: Account, amount: float) -> Account:
        """Internal withdraw operation"""
        if account.balance < amount:
            raise InsufficientFundsError(account.id, amount, account.balance)
        account.balance -= amount
        await self.session.flush()
        logger.info(f"Withdrew {amount} from account {account.id}, new balance: {account.balance} {self.session}")
        await self.session.refresh(account)
        return account

    async def _deposit(self, account: Account, amount: float) -> Account:
        """Internal deposit operation"""
        if amount == 10:
            raise AccountLockedError(account.id)
        account.balance += amount
        await self.session.flush()
        logger.info(f"Deposited {amount} to account {account.id}, new balance: {account.balance} {self.session}")
        await self.session.refresh(account)
        return account

    async def withdraw(self, account_id: int, amount: float) -> Account:
        """Withdraw money from an account"""
        try:
            async with self.db.transaction():
                account = await self.get_account_by_id(account_id)
                return await self._withdraw(account, amount)
        except SQLAlchemyError as e:
            logger.error(f"Database error during withdrawal: {str(e)}")
            raise DatabaseError(f"Failed to process withdrawal for account {account_id}")

    async def deposit(self, account_id: int, amount: float) -> Account:
        """Deposit money to an account"""
        try:
            async with self.db.transaction():
                account = await self.get_account_by_id(account_id)
                return await self._deposit(account, amount)
        except SQLAlchemyError as e:
            logger.error(f"Database error during deposit: {str(e)}")
            raise DatabaseError(f"Failed to process deposit for account {account_id}")

    async def transfer(self, from_account_id: int, to_account_id: int, amount: float) -> Dict[str, Any]:
        """Transfer money between accounts using unit of work pattern"""

        async with self.db.transaction():
            # Get both accounts
            from_account = await self.get_account_by_id(from_account_id)
            to_account = await self.get_account_by_id(to_account_id)

            # Perform withdrawal and deposit
            await self._withdraw(from_account, amount)
            await self._deposit(to_account, amount)

            return {
                "from_account": from_account_id,
                "to_account": to_account_id,
                "amount": amount,
                "status": "success"
            }
