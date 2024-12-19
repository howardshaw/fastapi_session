import logging

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends

from app.containers import Container
from app.schemas.transaction import TransactionRequest, TransactionResponse
from app.services import OrderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=TransactionResponse)
@inject
async def create_transaction(
        request: TransactionRequest,
        order_service: OrderService = Depends(Provide[Container.order_service]),
):
    logger.info(f"create_transaction {order_service}")
    result = await order_service.transaction(request.user_name, request.order_description, request.amount)
    return TransactionResponse(
        result=result,
    )
