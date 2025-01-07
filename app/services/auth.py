from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.logger import get_logger
from app.models.user import User
from app.services.user import UserService
from app.settings import Settings
from app.utils.hash import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

logger = get_logger(__name__)


class AuthService:
    def __init__(self, settings: Settings, user_service: UserService):
        self.settings = settings
        self.user_service = user_service

    def create_access_token(self, data: dict) -> str:
        """
        创建访问令牌
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.SECRET_KEY,
            algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        """
        user = await self.user_service.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def set_auth_cookie(self, response: Response, token: str) -> None:
        """
        设置认证cookie
        """
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            max_age=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=self.settings.COOKIE_SECURE,  # True in production
        )

    async def get_token_from_request(self, request: Request) -> Optional[str]:
        """
        从请求中获取token，支持cookie和bearer token
        """
        auth_cookie = request.cookies.get("access_token")
        if auth_cookie and auth_cookie.startswith("Bearer "):
            return auth_cookie.replace("Bearer ", "")

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "")

        return None

    async def get_current_user_from_request(
            self,
            request: Request,
    ) -> Optional[User]:
        """
        从请求中获取当前用户
        """
        token = await self.get_token_from_request(request)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        user = await self.user_service.get_user_by_email(email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user
