from typing import Dict, Any

from app.core.database import Database
from app.logger import get_logger
from app.models.order import Order
from app.models.user import User
from app.repositories import UserRepository, OrderRepository
from app.schemas.user import UserCreate
from app.utils.hash import hash_password

logger = get_logger(__name__)


class OrderService:
    def __init__(self, db: Database, user_repository: UserRepository, order_repository: OrderRepository):
        self.db = db
        self.user_repository = user_repository
        self.order_repository = order_repository

    async def transaction(self, user_data: UserCreate, order_description: str, amount: float) -> Dict[str, Any]:
        """
        创建用户和订单的事务
        使用事务上下文管理器确保事务的完整性
        """
        async with self.db.transaction():
            logger.info(f"Transaction for {user_data.username} with description {order_description}")

            hashed_password = hash_password(user_data.password)
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["hashed_password"] = hashed_password
            # 创建用户
            user = await self.user_repository.create_user(User(**user_dict))
            logger.info(f"Created user: {user.id} {user.username}")

            # 创建订单
            order = Order(
                user_id=user.id,
                description=order_description,
                amount=amount,
            )
            order = await self.order_repository.create_order(order)
            logger.info(f"Created order: {order.id} {order.user_id} {order.description}")

            return {
                "message": "Transaction successful",
                "user_id": user.id,
                "order_id": order.id,
                "amount": amount
            }
