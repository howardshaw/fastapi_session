from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, status, Response

from app.core.containers import Container
from app.logger.logger import get_logger
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import UserCreate, UserResponse
from app.services import UserService
from app.services.auth import AuthService

logger = get_logger(__name__)
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@inject
async def register(
        user_data: UserCreate,
        user_service: UserService = Depends(Provide[Container.services.user_service])
):
    """
    用户注册
    """
    try:
        # Check if user already exists
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        user = await user_service.create_user(user_data)
        return user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        ) from e


@router.post("/token", response_model=Token)
@inject
async def login(
        response: Response,
        login_data: LoginRequest,
        auth_service: AuthService = Depends(Provide[Container.services.auth_service])
):
    """
    用户登录
    """
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(
        data={"sub": user.email}
    )

    auth_service.set_auth_cookie(response, access_token)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
