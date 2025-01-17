from dependency_injector import containers, providers

from app.core.database import Database
from app.repositories import (
    AccountRepository,
    DatasetRepository,
    OrderRepository,
    ResourceRepository,
    UserRepository,
    WorkspaceRepository
)


class RepositoriesContainer(containers.DeclarativeContainer):
    """Repository related dependencies container."""

    db = providers.Dependency(instance_of=Database)

    account_repository = providers.Factory(
        AccountRepository,
        session_or_factory=db.provided.get_session,
    )
    dataset_repository = providers.Factory(
        DatasetRepository,
        session_or_factory=db.provided.get_session,
    )

    order_repository = providers.Factory(
        OrderRepository,
        session_or_factory=db.provided.get_session,
    )
    resource_repository = providers.Factory(
        ResourceRepository,
        session_or_factory=db.provided.get_session,
    )
    user_repository = providers.Factory(
        UserRepository,
        session_or_factory=db.provided.get_session,
    )
    workspace_repository = providers.Factory(
        WorkspaceRepository,
        session_or_factory=db.provided.get_session,
    )
