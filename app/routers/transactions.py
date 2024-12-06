from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends

from app.containers import Container
from app.repositories import RepositoryA, RepositoryB
from app.unit_of_work import UnitOfWork

router = APIRouter()


@router.post("/")
@inject
async def create_transaction(
        user_name: str,
        order_description: str,
        uow: UnitOfWork = Depends(Provide[Container.unit_of_work]),
        repo_a: RepositoryA = Depends(Provide[Container.repository_a]),
        repo_b: RepositoryB = Depends(Provide[Container.repository_b]),
):
    async with uow.transaction():
        user = await repo_a.create_user(user_name)
        print(f"user {user.id} {user.name}")
        order = await repo_b.create_order(user_id=user.id, description=order_description)
        print(f"order: {order.id} {order.user_id} {order.description}")
        return {"message": "Transaction successful", "user_id": user.id}
