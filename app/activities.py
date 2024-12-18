from dataclasses import dataclass

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.exceptions import InsufficientFundsError, AccountNotFoundError,AccountLockedError
from app.services import TransactionService


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
    def __init__(self, transaction_service: TransactionService):
        self.account_service = transaction_service

    @activity.defn
    async def withdraw_activity(
            self,
            account_id: int,
            amount: float
    ):
        try:
            await self.account_service.withdraw(account_id, amount)
        except (InsufficientFundsError, AccountNotFoundError) as e:
            # 将业务异常转换为可序列化的格式
            raise ApplicationError(
                "BusinessError",
                ActivityError.from_exception(e)
            )

    @activity.defn
    async def deposit_activity(
            self,
            account_id: int,
            amount: float
    ):
        try:
            await self.account_service.deposit(account_id, amount)
        except AccountNotFoundError as e:
            raise ApplicationError(
                "BusinessError",
                ActivityError.from_exception(e)
            )

    @activity.defn
    async def transform_activity(
            self,
            from_account_id: int,
            to_account_id: int,
            amount: float
    ):
        try:
            await self.account_service.transfer(from_account_id, to_account_id, amount)
        except (InsufficientFundsError, AccountNotFoundError) as e:
            activity.logger.error(f"Business error in transform_activity: {type(e)} {e}")

            raise ApplicationError(
                "BusinessError",
                ActivityError.from_exception(e),
                non_retryable=True,
            )
        except AccountLockedError as e:
            activity.logger.error(f"Account locked error: {type(e)} {e}")
            raise e

