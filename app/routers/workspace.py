import uuid
from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.containers import Container
from app.core.auth import CurrentUser
from app.logger import get_logger
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse
)
from app.services.workspace import WorkspaceService

router = APIRouter(
    prefix="/workspaces",
    tags=["workspaces"],
)

logger = get_logger(__name__)


@router.post("", response_model=WorkspaceResponse)
@inject
async def create_workspace(
        workspace: WorkspaceCreate,
        current_user: CurrentUser,
        workspace_service: WorkspaceService = Depends(Provide[Container.workspace_service])
):
    """创建工作空间"""
    return await workspace_service.create_workspace(workspace, current_user.id)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def get_workspace(
        workspace_id: uuid.UUID,
        current_user: CurrentUser,
        workspace_service: WorkspaceService = Depends(Provide[Container.workspace_service])
):
    """获取特定工作空间"""
    workspace = await workspace_service.get_user_workspace(current_user.id, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.get("", response_model=WorkspaceListResponse)
@inject
async def get_workspaces(
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100,
        workspace_service: WorkspaceService = Depends(Provide[Container.workspace_service])
):
    """获取用户的工作空间列表"""
    workspaces = await workspace_service.get_user_workspaces(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    total = await workspace_service.count_user_workspaces(current_user.id)
    
    # 将每个 workspace 转换为 WorkspaceResponse
    workspace_responses = [WorkspaceResponse.model_validate(workspace) for workspace in workspaces]
    
    return WorkspaceListResponse(
        items=workspace_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def update_workspace(
        workspace_id: uuid.UUID,
        workspace: WorkspaceUpdate,
        current_user: CurrentUser,
        workspace_service: WorkspaceService = Depends(Provide[Container.workspace_service])
):
    """更新工作空间"""
    updated_workspace = await workspace_service.update_workspace(
        current_user.id,
        workspace_id,
        workspace
    )
    if updated_workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return updated_workspace


@router.delete("/{workspace_id}", response_model=WorkspaceResponse)
@inject
async def delete_workspace(
        workspace_id: uuid.UUID,
        current_user: CurrentUser,
        workspace_service: WorkspaceService = Depends(Provide[Container.workspace_service])
):
    """删除工作空间"""
    deleted_workspace = await workspace_service.delete_workspace(
        current_user.id,
        workspace_id
    )
    if deleted_workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return deleted_workspace
