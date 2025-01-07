import uuid
from datetime import datetime

from sqlalchemy import func, DateTime, CHAR
from sqlmodel import Field, SQLModel

from app.utils.uuid6 import uuid7


class BaseModel(SQLModel):
    """Base model for all database models"""

    id: uuid.UUID = Field(
        default_factory=uuid7,
        sa_type=CHAR(36),
        primary_key=True,
        index=True,
        nullable=False,
        description="id"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "comment": "创建时间"},
        description="创建时间"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now(), "comment": "更新时间"},
        description="更新时间"
    )
