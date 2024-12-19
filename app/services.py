import logging
import time
from typing import Dict, Any

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AccountNotFoundError, DatabaseError, InsufficientFundsError, AccountLockedError
from app.models import User, Account
from app.repositories import UserRepository, OrderRepository
from app.schemas.user import UserCreate
from app.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, session: AsyncSession, uow: UnitOfWork):
        self.session = session
        self.uow = uow

    async def create_user(self, user_data: UserCreate):
        async with self.uow.transaction():
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

            # Create associated account
            db_account = Account(
                user=db_user,
                balance=0.0
            )
            self.session.add(db_account)
            await self.session.flush()

            await self.session.refresh(db_user)
            return db_user

    async def get_user_by_email(self, email: str):
        """Read-only operation to get user by email"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int):
        """Read-only operation to get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class TransactionService:
    def __init__(self, session: AsyncSession, uow: UnitOfWork):
        self.session = session
        self.uow = uow

    async def get_account_by_id(self, account_id: int) -> Account | None:
        """Get account by ID"""
        try:
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
        logger.info(f"Withdrew {amount} from account {account.id}, new balance: {account.balance}")
        return account

    async def _deposit(self, account: Account, amount: float) -> Account:
        """Internal deposit operation"""
        if amount == 10:
            raise AccountLockedError(account.id)
        account.balance += amount
        await self.session.flush()
        logger.info(f"Deposited {amount} to account {account.id}, new balance: {account.balance}")
        return account

    async def withdraw(self, account_id: int, amount: float) -> Account:
        """Withdraw money from an account"""
        try:
            async with self.uow.transaction():
                account = await self.get_account_by_id(account_id)
                return await self._withdraw(account, amount)
        except SQLAlchemyError as e:
            logger.error(f"Database error during withdrawal: {str(e)}")
            raise DatabaseError(f"Failed to process withdrawal for account {account_id}")

    async def deposit(self, account_id: int, amount: float) -> Account:
        """Deposit money to an account"""
        try:
            async with self.uow.transaction():
                account = await self.get_account_by_id(account_id)
                return await self._deposit(account, amount)
        except SQLAlchemyError as e:
            logger.error(f"Database error during deposit: {str(e)}")
            raise DatabaseError(f"Failed to process deposit for account {account_id}")

    async def transfer(self, from_account_id: int, to_account_id: int, amount: float) -> Dict[str, Any]:
        """Transfer money between accounts using unit of work pattern"""

        async with self.uow.transaction():
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
    def __init__(self, uow: UnitOfWork, user_repository: UserRepository, order_repository: OrderRepository):
        self.uow = uow
        self.user_repository = user_repository
        self.order_repository = order_repository

    async def transaction(self, user_name: str, order_description: str, amount: float) -> Dict[str, Any]:
        async with self.uow.transaction():
            user = await self.user_repository.create_user(user_name)
            logger.info(f"user {user.id} {user.username}")
            time.sleep(10)
            order = await self.order_repository.create_order(user_id=user.id, description=order_description,
                                                             amount=amount)
            logger.info(f"order: {order.id} {order.user_id} {order.description}")
            return {"message": "Transaction successful", "user_id": user.id, "order_id": order.id, "amount": amount}
