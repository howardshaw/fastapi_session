from dependency_injector import containers, providers

from app.core.database import Database
from app.services import (
    AuthService,
    OrderService,
    UserService,
    TransactionService,
    WorkspaceService,
    DatasetService,
    ChatService,
    MinioStorageService,
    ResourceService,
    MySQLDocumentStore
)
from app.settings import Settings


class ServicesContainer(containers.DeclarativeContainer):
    """Services related dependencies container."""

    repositories = providers.DependenciesContainer()
    db = providers.Dependency(instance_of=Database)
    settings = providers.Dependency(instance_of=Settings)

    storage_service = providers.Selector(
        settings.provided.STORAGE.PROVIDER,
        minio=providers.Singleton(
            MinioStorageService,
            settings=settings.provided.STORAGE,
        ),
    )

    document_store = providers.Selector(
        settings.provided.DOCUMENT_STORE.PROVIDER,
        mysql=providers.Singleton(
            MySQLDocumentStore,
            settings=settings.provided.DOCUMENT_STORE
        )
    )

    order_service = providers.Factory(
        OrderService,
        db=db.provided,
        user_repository=repositories.user_repository,
        order_repository=repositories.order_repository,
    )
    user_service = providers.Factory(
        UserService,
        db=db.provided,
        user_repository=repositories.user_repository,
        account_repository=repositories.account_repository,
    )
    auth_service = providers.Factory(
        AuthService,
        settings=settings,
        user_service=user_service,
    )
    transaction_service = providers.Factory(
        TransactionService,
        db=db.provided,
    )
    workspace_service = providers.Factory(
        WorkspaceService,
        db=db.provided,
        workspace_repository=repositories.workspace_repository,
    )

    resource_service = providers.Factory(
        ResourceService,
        db=db.provided,
        resource_repository=repositories.resource_repository,
        storage_service=storage_service,
    )

    dataset_service = providers.Factory(
        DatasetService,
        db=db.provided,
        dataset_repository=repositories.dataset_repository,
        workspace_repository=repositories.workspace_repository,
    )

    chat_service = providers.Factory(
        ChatService,
    )
