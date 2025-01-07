import uuid

from sqlalchemy import Column, Float, String, CHAR
from sqlmodel import Field, Relationship

from .base import BaseModel


class Order(BaseModel, table=True):
    """订单模型"""
    __tablename__ = "orders"

    user_id: uuid.UUID = Field(
        nullable=False,
        sa_type=CHAR(36),
        foreign_key="users.id",
        description="所有者ID"
    )

    description: str = Field(
        sa_column=Column(String(128), nullable=False, comment="订单描述"),
        description="订单描述"
    )

    amount: float = Field(
        default=0.0,
        sa_column=Column(Float, comment="订单金额")
    )

    # Relationships
    user: "User" = Relationship(back_populates="orders")
