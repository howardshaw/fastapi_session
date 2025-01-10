from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.exceptions import UnauthorizedError
from app.services.auth import AuthService


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        auth_service: AuthService,
        exclude_paths: Optional[list[str]] = None
    ):
        super().__init__(app)
        self.auth_service = auth_service
        self.exclude_paths = exclude_paths or []

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        
        # 检查是否在排除路径中
        if any(path.startswith(exclude_path) for exclude_path in self.exclude_paths):
            return await call_next(request)

        # 验证token
        try:
            await self.auth_service.get_current_user_from_request(request)
        except Exception as e:
            raise UnauthorizedError()

        return await call_next(request) 