import uuid
from dataclasses import dataclass

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.core.exceptions import InsufficientFundsError, AccountNotFoundError, AccountLockedError
from app.services import TransactionService
from app.logger import get_logger
logger = get_logger(__name__)

@dataclass
class ActivityError:
    type: str
    message: str

    @classmethod
    def from_exception(cls, e: Exception) -> list[str]:
        """Convert exception to a list of [error_type, error_message]"""
        return [
            e.__class__.__name__,
            str(e)
        ]


class AccountActivities:
    """Account-related activities implementation"""

    def __init__(self, transaction_service: TransactionService):
        self._transaction_service = transaction_service

    @activity.defn
    async def withdraw_activity(self, account_id: uuid.UUID, amount: float) -> None:
        """Withdraw money from an account"""
        try:
            await self._transaction_service.withdraw(account_id, amount)
        except (InsufficientFundsError, AccountNotFoundError) as e:
            logger.error(f"Withdraw failed: {e}")
            raise ApplicationError(
                "BusinessError",
                ActivityError.from_exception(e)
            )

    @activity.defn
    async def deposit_activity(self, account_id: uuid.UUID, amount: float) -> None:
        """Deposit money to an account"""
        try:
            await self._transaction_service.deposit(account_id, amount)
        except AccountNotFoundError as e:
            logger.error(f"Deposit failed: {e}")
            raise ApplicationError(
                "BusinessError",
                ActivityError.from_exception(e)
            )

    @activity.defn
    async def transform_activity(
            self,
            from_account_id: uuid.UUID,
            to_account_id: uuid.UUID,
            amount: float
    ) -> None:
        """Transfer money between accounts"""
        try:
            await self._transaction_service.transfer(
                from_account_id,
                to_account_id,
                amount
            )
        except (InsufficientFundsError, AccountNotFoundError) as e:
            logger.error(f"Transfer failed: {e}")
            raise ApplicationError(
                "BusinessError",
                ActivityError.from_exception(e),
                non_retryable=True,
            )
        except AccountLockedError as e:
            logger.error(f"Account locked: {e}")
            raise
