import logging
from typing import Generator

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.repositories import RepositoryA, RepositoryB
from app.unit_of_work import UnitOfWork



DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(DATABASE_URL)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session(
        sessionmaker=async_sessionmaker(engine, expire_on_commit=False)
) -> Generator[AsyncSession, None, None]:
    async with sessionmaker() as session:
        yield session




# 定义容器
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.main",
            "app.routers.transactions",
            "app.routers.users",
        ]
    )

    engine = providers.Singleton(
        create_async_engine,
        url=DATABASE_URL,
    )

    sessionmaker = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        expire_on_commit=False,
    )

    session = providers.Resource(
        get_session,
        sessionmaker=sessionmaker,
    )

    # RepositoryA
    repository_a = providers.Factory(
        RepositoryA,
        session=session.provided
    )

    # RepositoryB
    repository_b = providers.Factory(
        RepositoryB,
        session=session.provided
    )

    unit_of_work = providers.Factory(
        UnitOfWork,
        session=session.provided
    )

