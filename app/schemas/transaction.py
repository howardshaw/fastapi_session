from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    user_name: str = Field(..., description="User name")
    order_description:  str= Field(..., description="Order description")
    amount: float = Field(..., gt=0, description="Amount for the transaction")


class TransactionResponse(BaseModel):
    result: dict | None = None
