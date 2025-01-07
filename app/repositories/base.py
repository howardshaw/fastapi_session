import uuid
from typing import TypeVar, Type, Any, Callable

from sqlalchemy import select, func, update as sqlalchemy_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import DuplicatedError, NotFoundError
from app.logger import get_logger
from app.models.base import BaseModel
from app.utils.query_builder import dict_to_sqlalchemy_filter_options

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseRepository:
    def __init__(self, session_or_factory: AsyncSession | Callable[[], AsyncSession], model: Type[T]) -> None:
        self._session_or_factory = session_or_factory
        self.model = model

    @property
    def session(self) -> AsyncSession:
        """获取数据库会话"""
        if isinstance(self._session_or_factory, AsyncSession):
            return self._session_or_factory
        return self._session_or_factory()
    
    def filter(self, **kwargs):
        """
        创建基础查询过滤器
        
        Args:
            **kwargs: 过滤条件
            
        Returns:
            过滤后的查询对象
        """
        return select(self.model).filter_by(**kwargs)

    async def read_by_options(self, schema: T, eager: bool = False) -> dict:
        schema_as_dict: dict = schema.dict(exclude_none=True)
        ordering: str = schema_as_dict.get("ordering", "-id")
        order_query = (
            getattr(self.model, ordering[1:]).desc()
            if ordering.startswith("-")
            else getattr(self.model, ordering).asc()
        )
        page = schema_as_dict.get("page", 1)
        page_size = schema_as_dict.get("page_size", 10)
        filter_options = dict_to_sqlalchemy_filter_options(self.model, schema.dict(exclude_none=True))

        stmt = select(self.model).filter(filter_options).order_by(order_query)
        if eager:
            for eager_relation in getattr(self.model, "eagers", []):
                stmt = stmt.options(joinedload(getattr(self.model, eager_relation)))

        if page_size != "all":
            stmt = stmt.limit(page_size).offset((page - 1) * page_size)

        result = await self.session.execute(stmt)
        founds = result.scalars().all()

        # 获取总计数

        total_count_stmt = select(func.count()).select_from(self.model).filter(filter_options)
        total_count_result = await self.session.execute(total_count_stmt)
        total_count = total_count_result.scalar()

        return {
            "founds": founds,
            "search_options": {
                "page": page,
                "page_size": page_size,
                "ordering": ordering,
                "total_count": total_count,
            },
        }

    async def read_by_id(self, id: uuid.UUID, eager: bool = False):
        stmt = select(self.model).filter(self.model.id == str(id))
        if eager:
            for eager_relation in getattr(self.model, "eagers", []):
                stmt = stmt.options(joinedload(getattr(self.model, eager_relation)))

        result = await self.session.execute(stmt)
        found = result.scalars().first()
        if not found:
            raise NotFoundError(detail=f"not found id : {id}")
        return found

    async def create(self, schema: T):
        instance = self.model(**schema.dict())
        try:
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
        except IntegrityError as e:
            raise DuplicatedError(detail=str(e.orig))
        return instance

    async def update(self, id: uuid.UUID, schema: T):
        stmt = select(self.model).filter(self.model.id == str(id))
        result = await self.session.execute(stmt)
        instance = result.scalars().first()
        if not instance:
            raise NotFoundError(detail=f"not found id : {id}")

        update_stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.id == id)
            .values(**schema.dict(exclude_none=True))
        )

        await self.session.execute(update_stmt)
        await self.session.flush()
        return await self.read_by_id(id)

    async def update_attr(self, id: uuid.UUID, column: str, value: Any):
        stmt = select(self.model).filter(self.model.id == str(id))
        result = await self.session.execute(stmt)
        instance = result.scalars().first()
        if not instance:
            raise NotFoundError(detail=f"not found id : {id}")
        update_stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.id == id)
            .values({column: value})
        )
        await self.session.execute(update_stmt)
        await self.session.flush()
        return await self.read_by_id(id)

    async def whole_update(self, id: uuid.UUID, schema: T):
        stmt = select(self.model).filter(self.model.id == str(id))
        result = await self.session.execute(stmt)
        instance = result.scalars().first()
        if not instance:
            raise NotFoundError(detail=f"not found id : {str(id)}")
        update_stmt = (
            sqlalchemy_update(self.model)
            .where(self.model.id == id)
            .values(**schema.dict())
        )
        await self.session.execute(update_stmt)
        await self.session.flush()
        return await self.read_by_id(id)

    async def delete_by_id(self, id: uuid.UUID):
        stmt = select(self.model).filter(self.model.id == str(id))
        result = await self.session.execute(stmt)
        instance = result.scalars().first()
        if not instance:
            raise NotFoundError(detail=f"not found id : {str(id)}")
        await self.session.delete(instance)
        await self.session.flush()
        return instance

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        query = None
    ) -> list[T]:
        """
        获取多条记录，支持分页
        
        Args:
            skip: 跳过记录数
            limit: 返回记录数限制
            query: 可选的查询对象，如果为None则查询所有记录
            
        Returns:
            记录列表
        """
        if query is None:
            query = select(self.model)
            
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
