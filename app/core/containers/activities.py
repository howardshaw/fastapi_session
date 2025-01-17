from dependency_injector import containers, providers

from app.core.database import Database
from app.settings import Settings
from app.workflows.dsl.activities import (
    LoadDocumentActivity,
    SplitDocumentsActivity,
    TransformDocumentsActivity,
    VectorStoreActivity,
    StoreDocumentsActivity,
    RetrieveActivity,
)
from app.workflows.transfer.activities import AccountActivities
from app.workflows.translate.activities import TranslateActivities


class ActivitiesContainer(containers.DeclarativeContainer):
    """Activity related dependencies container."""

    repositories = providers.DependenciesContainer()
    services = providers.DependenciesContainer()
    clients = providers.DependenciesContainer()
    ai = providers.DependenciesContainer()
    db = providers.Dependency(instance_of=Database)
    settings = providers.Dependency(instance_of=Settings)

    # Activities
    account_activities = providers.Factory(
        AccountActivities,
        transaction_service=services.transaction_service
    )

    translate_activities = providers.Factory(
        TranslateActivities,
        llm=ai.provided.llm,
        redis_client=clients.redis_client
    )

    # Document Processing Activities
    load_document_activity = providers.Singleton(
        LoadDocumentActivity,
        storage_service=services.storage_service,
        resource_repository=repositories.resource_repository,
    )

    split_documents_activity = providers.Singleton(
        SplitDocumentsActivity,
    )

    store_documents_activity = providers.Singleton(
        StoreDocumentsActivity,
        doc_store=services.document_store,
    )

    transform_activity = providers.Singleton(
        TransformDocumentsActivity,
        llm=ai.llm,
    )

    vector_store_activity = providers.Singleton(
        VectorStoreActivity,
        embedding_service=ai.embedding_service,
        vector_store_settings=settings.provided.VECTOR_STORE,
    )

    retrieve_activity = providers.Singleton(
        RetrieveActivity,
        doc_store=services.document_store,
        embedding_service=ai.embedding_service,
        vector_store_settings=settings.provided.VECTOR_STORE,
    )
