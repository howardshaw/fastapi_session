import uuid
from enum import Enum
from typing import Dict, Any

from sqlmodel import Field, Relationship, Column, String, CHAR, JSON, UniqueConstraint

from .base import BaseModel


class DatasetType(str, Enum):
    VECTOR = "vector"  # 向量知识库
    FAQ = "faq"  # FAQ问答库
    TERMINOLOGY = "terminology"  # 术语库
    KNOWLEDGE_GRAPH = "knowledge_graph"  # 知识图谱库


class Dataset(BaseModel, table=True):
    __tablename__ = "datasets"

    __table_args__ = (UniqueConstraint("name", "workspace_id"),)

    name: str = Field(
        sa_column=Column(String(128), nullable=False, index=True, comment="知识库名称"),
        description="知识库名称"
    )
    description: str = Field(
        default="",
        sa_column=Column(String(512), nullable=True, comment="知识库描述"),
        description="知识库描述"
    )
    icon: str = Field(
        default="",
        sa_column=Column(String(255), nullable=True, comment="知识库图标"),
        description="知识库图标URL"
    )
    type: DatasetType = Field(
        sa_column=Column(String(32), nullable=False, comment="知识库类型"),
        description="知识库类型"
    )

    # 配置信息，包括解析、切分、索引、召回等配置
    config: Dict[str, Any] = Field(
        default={},
        sa_column=Column(JSON, nullable=True, comment="知识库配置"),
        description="知识库配置"
    )

    # 外键关联
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
        description="所有者ID"
    )

    # 关系
    workspace: "Workspace" = Relationship(back_populates="datasets")
    user: "User" = Relationship()
