from datetime import datetime
import uuid
from typing import Optional, Dict

from pydantic import BaseModel, Field, ConfigDict

from app.models.resource import StorageType, ResourceType


class ResourceBase(BaseModel):
    """资源基础模型"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., description="资源名称")


class ResourceCreate(ResourceBase):
    """创建资源请求模型"""
    model_config = ConfigDict(from_attributes=True)
    
    storage_type: StorageType = Field(default=StorageType.MINIO, description="存储类型")
    meta_info: Dict = Field(default=dict, description="元数据")


class ResourceUpdate(BaseModel):
    """更新资源请求模型"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, description="资源名称")
    description: Optional[str] = Field(None, description="资源描述")
    meta_info: Optional[Dict] = Field(default=dict, description="元数据")


class ResourceResponse(ResourceBase):
    """资源响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(..., description="资源ID")
    storage_type: StorageType = Field(..., description="存储类型")
    resource_type: ResourceType = Field(..., description="资源类型")
    size: int = Field(..., description="文件大小(字节)")
    mime_type: str = Field(..., description="MIME类型")
    meta_info: Optional[Dict] = Field(default=dict, description="元数据")
    workspace_id: uuid.UUID = Field(..., description="所属工作空间ID")
    user_id: uuid.UUID = Field(..., description="上传用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ResourceListResponse(BaseModel):
    """资源列表响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    items: list[ResourceResponse] = Field(..., description="资源列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="限制数量")


class ResourceUploadResponse(ResourceResponse):
    """资源上传响应模型"""
    url: str = Field(..., description="资源访问URL")


class ResourceURL(BaseModel):
    """资源URL响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    url: str = Field(..., description="资源访问URL")
    expires_at: datetime = Field(..., description="URL过期时间")


class ResourceQuery(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
    url_expire: int = Field(default=3600, ge=1, description="URL过期时间(秒)")


class ResourceUpload(BaseModel):
    meta_info: Optional[Dict] = Field(default=None, description="资源元信息") 