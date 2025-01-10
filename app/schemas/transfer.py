import uuid

from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    from_account: uuid.UUID = Field(..., description="Source account ID")
    to_account: uuid.UUID = Field(..., description="Destination account ID")
    amount: float = Field(..., gt=0, description="Amount to transfer")


class TransferResponse(BaseModel):
    workflow_id: str
    result: dict | None = None
    status: str
