from typing import Optional, List

from sqlmodel import Column
from sqlmodel import Field, Relationship, String

from .base import BaseModel


class User(BaseModel, table=True):
    """用户模型"""
    __tablename__ = "users"

    username: str = Field(
        sa_column=Column(String(128), unique=True, index=True, nullable=False, comment="User name")
    )
    email: str = Field(
        sa_column=Column(String(128), unique=True, index=True, nullable=False, comment="User email address")
    )
    hashed_password: str = Field(
        sa_column=Column(String(128), nullable=False, comment="User password hash")
    )

    # Relationships
    account: "Account" = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )
    orders: List["Order"] = Relationship(back_populates="user")
