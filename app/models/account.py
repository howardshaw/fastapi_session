from sqlalchemy import Column
from sqlmodel import Field, Relationship, ForeignKey, Integer, Float

from .base import BaseModel


class Account(BaseModel, table=True):
    """账户模型"""
    __tablename__ = "accounts"

    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
            comment="User ID"
        )
    )
    balance: float = Field(
        sa_column=Column(
            Float,
            nullable=False,
            default=0.0,
            comment="Account balance"
        )
    )

    # Relationships
    user: "User" = Relationship(back_populates="account")
