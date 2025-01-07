import uuid

from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)

class UserCreate(UserBase):
    password: constr(min_length=8)

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
