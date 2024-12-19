from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from app.clients import TemporalClientFactory
from app.repositories import UserRepository, OrderRepository
from app.services import UserService, TransactionService, OrderService
from app.settings import get_settings
from app.unit_of_work import UnitOfWork
from app.workflows.transfer.activities import AccountActivities
from app.workflows.translate.activities import TranslateActivities


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.main",
            "app.routers.users",
            "app.routers.transactions",
            "app.routers.translate",
            "app.routers.transform",
            "app.workflows.transfer.worker",
            "app.workflows.translate.worker",
        ]
    )

    # Configuration
    config = providers.Configuration()
    settings = providers.Singleton(get_settings)

    # Clients
    temporal_client = providers.Factory(
        TemporalClientFactory.create,
        url=settings.provided.TEMPORAL_HOST,
    )

    redis_client = providers.Factory(
        Redis.from_url,
        url=settings.provided.REDIS_URL,
    )

    # LLM
    llm = providers.Factory(
        ChatOpenAI,
        api_key=settings.provided.OPENAI_API_KEY,
        base_url=settings.provided.OPENAI_BASE_URL,
        model=settings.provided.OPENAI_MODEL,
    )

    # Database engine with async pool
    engine = providers.Singleton(
        create_async_engine,
        url=settings.provided.DATABASE_URL,
        echo=True,
        poolclass=AsyncAdaptedQueuePool,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
    )

    # Session factory
    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Session provider - creates new session for each request
    session = providers.Factory(
        session_factory.provided,
    )

    # Unit of Work - gets new session for each request
    unit_of_work = providers.Factory(
        UnitOfWork,
        session=session
    )

    # Repositories - get new session for each request
    user_repository = providers.Factory(
        UserRepository,
        session=session
    )

    order_repository = providers.Factory(
        OrderRepository,
        session=session
    )

    # Services - get new session for each request
    user_service = providers.Factory(
        UserService,
        session=session,
        uow=unit_of_work
    )

    order_service = providers.Factory(
        OrderService,
        session=session,
        uow=unit_of_work,
        user_repository=user_repository,
        order_repository=order_repository
    )

    transaction_service = providers.Factory(
        TransactionService,
        session=session,
        uow=unit_of_work
    )

    # Activities
    account_activities = providers.Factory(
        AccountActivities,
        transaction_service=transaction_service
    )

    translate_activities = providers.Factory(
        TranslateActivities,
        llm=llm,
        redis_client=redis_client
    )
