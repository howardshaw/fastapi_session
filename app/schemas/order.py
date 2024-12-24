"""
订单相关的数据模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class OrderBase(BaseModel):
    """订单基础模型"""
    description: str = Field(..., description="订单描述")
    amount: float = Field(..., ge=0, description="订单金额")


class OrderCreate(OrderBase):
    """创建订单模型"""
    user_id: int = Field(..., description="用户ID")


class OrderUpdate(OrderBase):
    """更新订单模型"""
    description: Optional[str] = Field(None, description="订单描述")
    amount: Optional[float] = Field(None, ge=0, description="订单金额")


class OrderInDB(OrderBase):
    """数据库订单模型"""
    id: int
    user_id: int
    
    class Config:
        from_attributes = True
