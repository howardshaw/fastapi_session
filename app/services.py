import logging
from typing import Dict, Any, Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Database
from app.exceptions import AccountNotFoundError, DatabaseError, InsufficientFundsError, AccountLockedError
from app.models import User, Account
from app.repositories import UserRepository, OrderRepository
from app.schemas.user import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


class OrderService:
    def __init__(self, db: Database, user_repository: UserRepository, order_repository: OrderRepository):
        self.db = db
        self.user_repository = user_repository
        self.order_repository = order_repository

    async def transaction(self, user_name: str, order_description: str, amount: float) -> Dict[str, Any]:
        """
        创建用户和订单的事务
        使用事务上下文管理器确保事务的完整性
        """
        async with self.db.transaction():
            logger.info(f"Transaction for {user_name} with description {order_description}")

            # 创建用户
            user = await self.user_repository.create_user(user_name)
            logger.info(f"Created user: {user.id} {user.username}")

            # 创建订单
            order = await self.order_repository.create_order(
                user_id=user.id,
                description=order_description,
                amount=amount,
            )
            logger.info(f"Created order: {order.id} {order.user_id} {order.description}")

            return {
                "message": "Transaction successful",
                "user_id": user.id,
                "order_id": order.id,
                "amount": amount
            }
