from pydantic import BaseModel, Field


class TransferRequest(BaseModel):
    from_account: int = Field(..., description="Source account ID")
    to_account: int = Field(..., description="Destination account ID")
    amount: float = Field(..., gt=0, description="Amount to transfer")


class TransferResponse(BaseModel):
    workflow_id: str
    result: dict | None = None
    status: str
