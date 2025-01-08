import uuid
from typing import List

from sqlmodel import Field, Relationship, Column, String, CHAR

from .base import BaseModel


class Workspace(BaseModel, table=True):
    __tablename__ = "workspaces"

    name: str = Field(
        sa_column=Column(String(128), nullable=False, index=True, comment="空间名称"),
        description="空间名称"
    )
    description: str = Field(
        default="",
        sa_column=Column(
            String(128),
            nullable=True,
            comment="Workspace description"
        ),
        description="空间描述"
    )

    user_id: uuid.UUID = Field(
        nullable=False,
        sa_type=CHAR(36),
        foreign_key="users.id",
        description="所有者ID"
    )

    # Relationships
    user: "User" = Relationship()
    datasets: List["Dataset"] = Relationship(back_populates="workspace")
