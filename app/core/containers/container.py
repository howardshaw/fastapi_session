from dependency_injector import containers, providers

from app.core.containers.activities import ActivitiesContainer
from app.core.containers.ai import AIContainer
from app.core.containers.clients import ClientsContainer
from app.core.containers.database import DatabaseContainer
from app.core.containers.repositories import RepositoriesContainer
from app.core.containers.services import ServicesContainer
from app.settings import get_settings


class Container(containers.DeclarativeContainer):
    """Main container."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.main",
            "app.core.auth",
            "app.routers.users",
            "app.routers.auth",
            "app.routers.transactions",
            "app.routers.translate",
            "app.routers.transform",
            "app.routers.dsl",
            "app.routers.resource",
            "app.routers.workspace",
            "app.routers.dataset",
            "app.services.auth",
            "app.workflows.transfer.worker",
            "app.workflows.translate.worker",
            "app.workflows.dsl.worker",
            "app.routers.chat",
        ]
    )

    # Configuration
    config = providers.Configuration()
    settings = providers.Singleton(get_settings)

    database = providers.Container(
        DatabaseContainer,
        settings=settings.provided.DATABASE,
    )

    repositories = providers.Container(
        RepositoriesContainer,
        db=database.db,
    )

    clients = providers.Container(
        ClientsContainer,
        settings=settings,
    )

    ai = providers.Container(
        AIContainer,
        settings=settings,
    )

    services = providers.Container(
        ServicesContainer,
        settings=settings,
        db=database.db,
        repositories=repositories,
    )

    activities = providers.Container(
        ActivitiesContainer,
        settings=settings,
        db=database.db,
        ai=ai,
        clients=clients,
        services=services,
        repositories=repositories,
    )
