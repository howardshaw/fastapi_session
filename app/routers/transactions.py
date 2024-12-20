import logging

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.containers import Container
from app.database import Database
from app.schemas.transaction import TransactionRequest, TransactionResponse
from app.services import OrderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=TransactionResponse)
@inject
async def create_transaction(
        request: TransactionRequest,
        db: Database = Depends(Provide[Container.db]),
        order_service: OrderService = Depends(Provide[Container.order_service]),
):
    """Create a new transaction."""
    # 测试查询 - 使用普通 session
    async with db.session() as session:
        result = await session.execute(text("SELECT 1"))
        row = result.scalar()
        logger.info(f"Query test: {id(session)}, result: {row}")

    async with db.session() as session:
        result = await session.execute(text("SELECT 2"))
        row = result.scalar()
        logger.info(f"Query test2: {id(session)}, result: {row}")
    # 测试事务 - 使用 transaction session
    async with db.transaction() as session:
        result = await session.execute(text("SELECT 2"))
        row = result.scalar()
        logger.info(f"Transaction test: {id(session)}, result: {row}")
        # 模拟一些事务操作
        await session.execute(text("SELECT 3"))

    async with db.transaction() as session:
        result = await session.execute(text("SELECT 2"))
        row = result.scalar()
        logger.info(f"Transaction test2: {id(session)}, result: {row}")
        # 模拟一些事务操作
        await session.execute(text("SELECT 3"))

    # 执行实际的业务事务
    logger.info(f"start real business\n\n\n\n")
    result = await order_service.transaction(request.user_name, request.order_description, request.amount)
    return TransactionResponse(
        result=result,
    )
