import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, StringConstraints, Field
from typing_extensions import Annotated


# User schemas
class UserBase(BaseModel):
    email: EmailStr = Field(default="user@example.com", description="User's email address")
    username: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=50,
        ),
    ] = Field(default="user", description="User's name")


class UserCreate(UserBase):
    password: Annotated[
        str,
        StringConstraints(
            min_length=8
        ),
    ] = Field(default="defaultpassword", description="User's password")


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Account schemas
class AccountBase(BaseModel):
    balance: float = 0.0


class AccountCreate(AccountBase):
    user_id: uuid.UUID


class AccountResponse(AccountBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Order schemas
class OrderBase(BaseModel):
    description: str
    amount: float


class OrderCreate(OrderBase):
    user_id: uuid.UUID


class OrderResponse(OrderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Transaction schemas
class TransactionBase(BaseModel):
    amount: float


class WithdrawRequest(TransactionBase):
    pass


class DepositRequest(TransactionBase):
    pass
