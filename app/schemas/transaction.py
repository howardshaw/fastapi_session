from pydantic import BaseModel, Field

from .user import UserCreate


class TransactionRequest(BaseModel):
    user_data: UserCreate = Field(..., description="User create")
    order_description: str = Field(..., description="Order description")
    amount: float = Field(..., gt=0, description="Amount for the transaction")


class TransactionResponse(BaseModel):
    result: dict | None = None
