import logging

from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI
from redis.asyncio import Redis

from app.core.clients import TemporalClientFactory
from app.core.database import Database
from app.repositories import UserRepository, OrderRepository
from app.services import UserService, TransactionService, OrderService
from app.settings import get_settings
from app.workflows.transfer.activities import AccountActivities
from app.workflows.translate.activities import TranslateActivities

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    # Database
    db = providers.Singleton(
        Database,
        db_url=settings.provided.DATABASE_URL,
    )

    # Session provider
    # session = providers.Resource(
    #     db.provided._session_factory,
    # )

    # Repositories - get new session for each request
    user_repository = providers.Factory(
        UserRepository,
        session_or_factory=db.provided.get_session,
    )

    order_repository = providers.Factory(
        OrderRepository,
        session_or_factory=db.provided.get_session,
    )

    # Services - get new session for each request
    user_service = providers.Factory(
        UserService,
        db=db.provided,
        user_repository=user_repository,
    )

    order_service = providers.Factory(
        OrderService,
        db=db.provided,
        user_repository=user_repository,
        order_repository=order_repository
    )

    transaction_service = providers.Factory(
        TransactionService,
        db=db.provided,
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
