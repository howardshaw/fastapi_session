from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace

from app.core.containers import Container
from app.logger.logger import get_logger
from app.schemas.user import UserCreate, UserResponse
from app.services import UserService

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
def get_users():
    return {"message": "This is the users endpoint"}


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_user(
        user_data: UserCreate,
        user_service: UserService = Depends(Provide[Container.user_service])
):
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


@router.get("/me", response_model=UserResponse)
@inject
async def get_current_user(
        user_id: int,
        user_service: UserService = Depends(Provide[Container.user_service])
):
    logger.info(f"get current user {user_id} trace: {trace.get_current_span().get_span_context().trace_id}")

    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
