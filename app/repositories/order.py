from typing import Callable, Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderCreationError
from app.logger import get_logger
from app.models.order import Order
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class OrderRepository(BaseRepository):

    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession]) -> None:
        self._session_or_factory = session_or_factory
        super().__init__(session_or_factory, Order)

    async def create_order(self, order: Order) -> Order:
        logger.info(f"Creating order: {order}")

        # 业务规则验证
        if order.description == "First order":
            raise OrderCreationError("Cannot create order with description 'First order'")

        # 使用基类的 create 方法创建订单
        return await super().create(order)

    async def get_user_orders(
            self,
            user_id: int,
            *,
            skip: int = 0,
            limit: int = 100
    ) -> List[Order]:
        """
        获取用户的订单列表
        
        Args:
            user_id: 用户ID
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            订单列表
        """
        query = self.filter(user_id=user_id)
        return await self.get_multi(skip=skip, limit=limit, query=query)

    async def get_user_order(self, user_id: int, order_id: int) -> Optional[Order]:
        """
        获取用户的特定订单
        
        Args:
            user_id: 用户ID
            order_id: 订单ID
            
        Returns:
            订单对象，如果不存在返回 None
        """
        query = self.filter(id=order_id, user_id=user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_orders_by_amount(
            self,
            user_id: int,
            min_amount: Optional[float] = None,
            max_amount: Optional[float] = None,
            *,
            skip: int = 0,
            limit: int = 100
    ) -> List[Order]:
        """
        获取用户在指定金额范围内的订单
        
        Args:
            user_id: 用户ID
            min_amount: 最小金额
            max_amount: 最大金额
            skip: 跳过记录数
            limit: 返回记录数限制
            
        Returns:
            订单列表
        """
        query = select(Order).where(Order.user_id == user_id)

        if min_amount is not None:
            query = query.where(Order.amount >= min_amount)
        if max_amount is not None:
            query = query.where(Order.amount <= max_amount)

        return await self.get_multi(skip=skip, limit=limit, query=query)
