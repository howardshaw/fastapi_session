from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship,ForeignKey

from .base import BaseModel


class Order(BaseModel, table=True):
    """订单模型"""
    __tablename__ = "orders"

    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="User ID"
        )
    )
    description: str = Field(
        sa_column=Column(
            String(128),
            nullable=False,
            comment="Order description"
        )
    )
    amount: float = Field(
        sa_column=Column(
            Float,
            nullable=False,
            comment="Order amount"
        )
    )

    # Relationships
    user: "User" = Relationship(back_populates="orders")
