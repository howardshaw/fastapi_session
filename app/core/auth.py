from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Request

from app.core.containers import Container
from app.models.user import User
from app.services.auth import AuthService


@inject
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(Provide[Container.auth_service])
) -> User:
    """
    获取当前用户的依赖函数
    
    Returns:
        当前认证用户对象
    """
    return await auth_service.get_current_user_from_request(request)


# 创建类型别名，使用更简洁
CurrentUser = Annotated[User, Depends(get_current_user)] 