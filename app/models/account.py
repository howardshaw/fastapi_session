import uuid

from sqlalchemy import Column, CHAR
from sqlmodel import Field, Relationship, Float

from .base import BaseModel


class Account(BaseModel, table=True):
    """账户模型"""
    __tablename__ = "accounts"

    user_id: uuid.UUID = Field(
        sa_type=CHAR(36),
        nullable=False,
        foreign_key="users.id",
        description="所有者ID"
    )

    balance: float = Field(
        default=0.0,
        sa_column=Column(Float, comment="账户余额")
    )

    # Relationships
    user: "User" = Relationship(back_populates="account")
