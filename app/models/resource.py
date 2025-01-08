import uuid
from enum import Enum
from typing import TYPE_CHECKING, Dict

from sqlmodel import Field, Relationship, Column, String, Integer, CHAR, JSON

from .base import BaseModel

if TYPE_CHECKING:
    from .workspace import Workspace
    from .user import User


class StorageType(str, Enum):
    """存储类型"""
    MINIO = "minio"
    S3 = "s3"
    LOCAL = "local"


class ResourceType(str, Enum):
    """资源类型"""
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


class Resource(BaseModel, table=True):
    """资源模型"""
    __tablename__ = "resources"

    name: str = Field(
        sa_column=Column(String(256), nullable=False, index=True, comment="资源名称")
    )
    storage_type: StorageType = Field(
        sa_column=Column(String(20), nullable=False, comment="存储类型")
    )
    resource_type: ResourceType = Field(
        sa_column=Column(String(20), nullable=False, comment="资源类型")
    )
    size: int = Field(
        sa_column=Column(Integer, nullable=False, comment="文件大小(字节)")
    )
    path: str = Field(
        sa_column=Column(String(512), nullable=False, comment="存储路径")
    )
    mime_type: str = Field(
        sa_column=Column(String(128), nullable=False, comment="MIME类型")
    )
    meta_info: Dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, default={}, comment="元数据"),
        description="元数据"
    )

    workspace_id: uuid.UUID = Field(
        nullable=False,
        sa_type=CHAR(36),
        foreign_key="workspaces.id",
        description="所属工作空间ID"
    )
    user_id: uuid.UUID = Field(
        nullable=False,
        sa_type=CHAR(36),
        foreign_key="users.id",
        description="上传用户ID"
    )

    # Relationships
    workspace: "Workspace" = Relationship()
    user: "User" = Relationship()
