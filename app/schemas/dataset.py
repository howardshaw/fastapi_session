from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.dataset import DatasetType


class DatasetBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(..., description="知识库描述")
    icon: Optional[str] = Field(..., description="知识库icon")
    type: DatasetType
    config: Optional[Dict[str, Any]] = Field(..., description="知识库配置")


class DatasetCreate(DatasetBase):
    workspace_id: UUID


class DatasetUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    icon: Optional[str] = Field(None, description="知识库icon")
    config: Optional[Dict[str, Any]] = Field(None, description="知识库配置")


class DatasetResponse(DatasetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="知识库id")
    workspace_id: UUID = Field(..., description="知识库工作空间id")
    user_id: UUID = Field(..., description="知识库创建者id")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DatasetListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[DatasetResponse]
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")
