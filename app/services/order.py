import logging
from typing import Dict, Any

from app.core.database import Database
from app.repositories import UserRepository, OrderRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, db: Database, user_repository: UserRepository, order_repository: OrderRepository):
        self.db = db
        self.user_repository = user_repository
        self.order_repository = order_repository

    async def transaction(self, user_name: str, order_description: str, amount: float) -> Dict[str, Any]:
        """
        创建用户和订单的事务
        使用事务上下文管理器确保事务的完整性
        """
        async with self.db.transaction():
            logger.info(f"Transaction for {user_name} with description {order_description}")

            # 创建用户
            user = await self.user_repository.create_user(user_name)
            logger.info(f"Created user: {user.id} {user.username}")

            # 创建订单
            order = await self.order_repository.create_order(
                user_id=user.id,
                description=order_description,
                amount=amount,
            )
            logger.info(f"Created order: {order.id} {order.user_id} {order.description}")

            return {
                "message": "Transaction successful",
                "user_id": user.id,
                "order_id": order.id,
                "amount": amount
            }
