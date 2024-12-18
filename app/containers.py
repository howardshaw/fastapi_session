import logging
from typing import Generator

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.activities import AccountActivities
from app.clients import TemporalClientFactory
from app.repositories import UserRepository, OrderRepository
from app.services import UserService, TransactionService,OrderService
from app.settings import get_settings
from app.unit_of_work import UnitOfWork

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_session(
        sessionmaker: async_sessionmaker
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
            "app.routers.transform",
            "app.activities",
            "app.worker",
        ]
    )

    settings = providers.Singleton(get_settings)

    # Clients
    temporal_client = providers.Singleton(
        TemporalClientFactory.create,
        url=settings.provided.TEMPORAL_HOST,
    )

    # Database
    engine = providers.Singleton(
        create_async_engine,
        url=settings.provided.DATABASE_URL,
    )

    sessionmaker = providers.Singleton(
        async_sessionmaker,
        engine,
        expire_on_commit=False,
    )
    session = providers.Resource(
        get_session,
        sessionmaker=sessionmaker,
    )

    unit_of_work = providers.Factory(
        UnitOfWork,
        session=session.provided,
    )

    # Repositories
    user_repository = providers.Factory(
        UserRepository,
        session=session.provided,
    )

    order_repository = providers.Factory(
        OrderRepository,
        session=session.provided,
    )

    # Services
    user_service = providers.Factory(
        UserService,
        session=session.provided,
        uow=unit_of_work,
    )
    order_service = providers.Factory(
        OrderService,
        uow=unit_of_work,
        user_repository=user_repository,
        order_repository=order_repository,
    )

    transaction_service = providers.Factory(
        TransactionService,
        session=session.provided,
        uow=unit_of_work,
    )

    # Activities
    account_activities = providers.Factory(
        AccountActivities,
        transaction_service=transaction_service,
    )
