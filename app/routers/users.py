from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException, status
from opentelemetry import trace

from app.core.auth import CurrentUser
from app.core.containers import Container
from app.logger.logger import get_logger
from app.schemas.user import UserResponse
from app.services import UserService

logger = get_logger(__name__)
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
def get_users():
    return {"message": "This is the users endpoint"}


@router.get("/me", response_model=UserResponse)
@inject
async def get_current_user(
        current_user: CurrentUser,
        user_service: UserService = Depends(Provide[Container.user_service])
):
    logger.info(f"get current user {current_user.id} trace: {trace.get_current_span().get_span_context().trace_id}")

    user = await user_service.get_user_by_id(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
