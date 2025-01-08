import uuid

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import CurrentUser
from app.core.containers import Container
from app.logger import get_logger
from app.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetListResponse
)
from app.services.dataset import DatasetService

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
)

logger = get_logger(__name__)


@router.post("", response_model=DatasetResponse)
@inject
async def create_dataset(
        dataset: DatasetCreate,
        current_user: CurrentUser,
        dataset_service: DatasetService = Depends(Provide[Container.dataset_service])
):
    """创建知识库"""
    return await dataset_service.create_dataset(dataset, current_user.id)


@router.get("/workspace/{workspace_id}", response_model=DatasetListResponse)
@inject
async def get_workspace_datasets(
        workspace_id: uuid.UUID,
        current_user: CurrentUser,
        skip: int = 0,
        limit: int = 100,
        dataset_service: DatasetService = Depends(Provide[Container.dataset_service])
):
    """获取工作空间下的知识库列表"""
    datasets = await dataset_service.get_workspace_datasets(
        workspace_id=workspace_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    total = await dataset_service.count_workspace_datasets(
        workspace_id=workspace_id,
        user_id=current_user.id
    )
    
    return DatasetListResponse(
        items=[DatasetResponse.model_validate(d) for d in datasets],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
@inject
async def get_dataset(
        dataset_id: uuid.UUID,
        current_user: CurrentUser,
        dataset_service: DatasetService = Depends(Provide[Container.dataset_service])
):
    """获取特定知识库"""
    dataset = await dataset_service.get_user_dataset(current_user.id, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
@inject
async def update_dataset(
        dataset_id: uuid.UUID,
        dataset: DatasetUpdate,
        current_user: CurrentUser,
        dataset_service: DatasetService = Depends(Provide[Container.dataset_service])
):
    """更新知识库"""
    updated_dataset = await dataset_service.update_dataset(
        current_user.id,
        dataset_id,
        dataset
    )
    if updated_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return updated_dataset


@router.delete("/{dataset_id}", response_model=DatasetResponse)
@inject
async def delete_dataset(
        dataset_id: uuid.UUID,
        current_user: CurrentUser,
        dataset_service: DatasetService = Depends(Provide[Container.dataset_service])
):
    """删除知识库"""
    deleted_dataset = await dataset_service.delete_dataset(
        current_user.id,
        dataset_id
    )
    if deleted_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return deleted_dataset
