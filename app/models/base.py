from datetime import datetime

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    id: int = Field(primary_key=True)

    created_at: datetime = Field(
        default_factory=datetime.now, index=True, nullable=False
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, index=True, nullable=False
    )
