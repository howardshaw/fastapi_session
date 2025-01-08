import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi import Form

from app.core.auth import get_current_user
from app.core.containers import Container
from app.logger import get_logger
from app.models import User
from app.schemas.resource import (
    ResourceResponse,
    ResourceListResponse,
    ResourceUploadResponse,
    ResourceURL,
    ResourceUpdate,
    ResourceQuery
)
from app.services.resource import ResourceService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/resources",
    tags=["resources"],
)

logger = get_logger(__name__)


@router.post("", response_model=ResourceUploadResponse)
@inject
async def upload_resource(
        workspace_id: uuid.UUID,
        file: UploadFile = File(...),
        meta_info: Optional[str] = Form(None),
        current_user: User = Depends(get_current_user),
        resource_service: ResourceService = Depends(Provide[Container.resource_service])
):
    """上传资源文件"""
    meta_info_dict = None
    if meta_info:
        try:
            meta_info_dict = json.loads(meta_info)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid meta_info JSON format")

    logger.info(f"uploading {file.filename} {meta_info}")
    resource = await resource_service.upload_resource(
        file=file,
        workspace_id=workspace_id,
        user_id=current_user.id,
        meta_info=meta_info_dict
    )
    logger.info(f"resource id: {resource.id}")

    # 获取资源访问URL
    url = await resource_service.get_resource_url(
        resource_id=resource.id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        expire=timedelta(days=7)
    )

    return ResourceUploadResponse(
        **resource.model_dump(),
        url=url
    )


@router.get("", response_model=ResourceListResponse)
@inject
async def list_resources(
        workspace_id: uuid.UUID,
        query: ResourceQuery = Depends(),
        current_user: User = Depends(get_current_user),
        resource_service: ResourceService = Depends(Provide[Container.resource_service])
):
    """获取工作空间的资源列表"""
    resources, urls, total = await resource_service.get_workspace_resources_with_urls(
        workspace_id=workspace_id,
        skip=query.skip,
        limit=query.limit,
        expire=query.url_expire
    )

    return ResourceListResponse(
        items=[
            ResourceUploadResponse(
                **resource.model_dump(),
                url=urls.get(resource.id, "")
            )
            for resource in resources
        ],
        total=total,
        skip=query.skip,
        limit=query.limit
    )


@router.delete("/{resource_id}", response_model=ResourceResponse)
@inject
async def delete_resource(
        workspace_id: uuid.UUID,
        resource_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        resource_service: ResourceService = Depends(Provide[Container.resource_service])
):
    """删除资源"""
    success = await resource_service.delete_resource(
        resource_id=resource_id,
        workspace_id=workspace_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Resource not found")


@router.get("/{resource_id}/url", response_model=ResourceURL)
@inject
async def get_resource_url(
        workspace_id: uuid.UUID,
        resource_id: uuid.UUID,
        expire: int = Query(3600, ge=1, description="URL过期时间(秒)"),
        current_user: User = Depends(get_current_user),
        resource_service: ResourceService = Depends(Provide[Container.resource_service])
):
    """获取资源访问URL"""
    url = await resource_service.get_resource_url(
        resource_id=resource_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        expire=timedelta(seconds=expire)
    )

    if not url:
        raise HTTPException(status_code=404, detail="Resource not found")

    expires_at = datetime.now() + timedelta(seconds=expire)

    return ResourceURL(
        url=url,
        expires_at=expires_at
    )


@router.patch("/{resource_id}", response_model=ResourceResponse)
@inject
async def update_resource(
        workspace_id: uuid.UUID,
        resource_id: uuid.UUID,
        resource_update: ResourceUpdate,
        current_user: User = Depends(get_current_user),
        resource_service: ResourceService = Depends(Provide[Container.resource_service])
):
    """更新资源信息"""
    updated = await resource_service.update_resource(
        resource_id=resource_id,
        workspace_id=workspace_id,
        user_id=current_user.id,
        update_data=resource_update
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found")
    return updated
