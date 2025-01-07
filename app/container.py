from dependency_injector import containers, providers

from app.core.database import Database
from app.repositories.workspace import WorkspaceRepository
from app.services.workspace import WorkspaceService


class Container(containers.DeclarativeContainer):
    # Core
    db = providers.Singleton(Database)

    # Repositories
    workspace_repository = providers.Factory(
        WorkspaceRepository,
        session_factory=db.provided.session_factory,
    )

    # Services
    workspace_service = providers.Factory(
        WorkspaceService,
        db=db,
        workspace_repository=workspace_repository,
    )
