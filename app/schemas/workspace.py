import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WorkspaceBase(BaseModel):
    """工作空间基础模型"""
    name: str
    description: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    """创建工作空间请求模型"""
    pass


class WorkspaceUpdate(BaseModel):
    """更新工作空间请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceResponse(WorkspaceBase):
    """工作空间响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WorkspaceListResponse(BaseModel):
    """工作空间列表响应模型"""
    model_config = ConfigDict(from_attributes=True)

    items: list[WorkspaceResponse]
    total: int
    skip: int
    limit: int
