from dependency_injector import containers, providers
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from redis.asyncio import Redis

from app.core.clients import TemporalClientFactory
from app.core.database import Database
from app.repositories import UserRepository, OrderRepository
from app.repositories.account import AccountRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.resource import ResourceRepository
from app.repositories.workspace import WorkspaceRepository
from app.services import (
    UserService,
    TransactionService,
    OrderService,
    WorkspaceService,
    ChatService,
)
from app.services.auth import AuthService
from app.services.dataset import DatasetService
from app.services.doc_store.mysql import MySQLDocumentStore
from app.services.document_decryption import SimpleDocumentDecryptionService
from app.services.document_processor import LangchainDocumentProcessor
from app.services.document_transform import (
    ContentCleanTransformer,
    ChunkSplitTransformer,
    HypotheticalQuestionTransformer,
    SummaryTransformer
)
from app.services.embeddings.huggingface import HuggingFaceEmbeddingService
from app.services.embeddings.openai import OpenAIEmbeddingService
from app.services.llm.claude_service import ClaudeService
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService
from app.services.resource import ResourceService
from app.services.storage import MinioStorageService
from app.services.vector_store.chroma import ChromaVectorStore
from app.services.vector_store.milvus import MilvusVectorStore
from app.services.vector_store.opensearch import OpenSearchVectorStore
from app.settings import get_settings
from app.workflows.dsl.activities import (
    LoadDocumentActivity,
    CleanContentActivity,
    SplitDocumentsActivity,
    HypotheticalQuestionActivity,
    GenerateSummaryActivity,
    VectorStoreActivity, StoreDocumentsActivity, RetrieveActivity,
)
from app.workflows.transfer.activities import AccountActivities
from app.workflows.translate.activities import TranslateActivities


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""
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

    # Clients
    temporal_client = providers.Resource(
        TemporalClientFactory.create,
        url=settings.provided.TEMPORAL.HOST,
        otlp_endpoint=settings.provided.OTLP.ENDPOINT,
    )

    redis_client = providers.Factory(
        Redis.from_url,
        url=settings.provided.REDIS_URL,
    )
    # LLM
    llm = providers.Factory(
        ChatOpenAI,
        api_key=settings.provided.LLM.OPENAI_API_KEY,
        base_url=settings.provided.LLM.OPENAI_BASE_URL,
        model=settings.provided.LLM.OPENAI_MODEL,
    )

    # LLM service
    llm_service = providers.Selector(
        settings.provided.LLM.PROVIDER,
        openai=providers.Singleton(
            OpenAIService,
            settings=settings.provided.LLM,
        ),
        ollama=providers.Singleton(
            OllamaService,
            settings=settings.provided.LLM,
        ),
        claude=providers.Singleton(
            ClaudeService,
            settings=settings.provided.LLM,
        ),
    )

    # Database
    db = providers.Singleton(
        Database,
        db_url=settings.provided.DATABASE.URL,
    )

    # Repositories - get new session for each request
    user_repository = providers.Factory(
        UserRepository,
        session_or_factory=db.provided.get_session,
    )

    order_repository = providers.Factory(
        OrderRepository,
        session_or_factory=db.provided.get_session,
    )

    account_repository = providers.Factory(
        AccountRepository,
        session_or_factory=db.provided.get_session,
    )

    workspace_repository = providers.Factory(
        WorkspaceRepository,
        session_or_factory=db.provided.get_session,
    )

    # Services
    user_service = providers.Factory(
        UserService,
        db=db.provided,
        user_repository=user_repository,
        account_repository=account_repository,
    )
    resource_repository = providers.Factory(
        ResourceRepository,
        session_or_factory=db.provided.get_session,
    )

    dataset_repository = providers.Singleton(
        DatasetRepository,
        session_or_factory=db.provided.get_session
    )

    # Auth dependencies
    auth_service = providers.Factory(
        AuthService,
        settings=settings,
        user_service=user_service,
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

    workspace_service = providers.Factory(
        WorkspaceService,
        db=db.provided,
        workspace_repository=workspace_repository,
    )

    storage_service = providers.Singleton(
        MinioStorageService,
        settings=settings.provided.MINIO,
    )

    resource_service = providers.Factory(
        ResourceService,
        db=db.provided,
        storage_service=storage_service,
        resource_repository=resource_repository
    )

    dataset_service = providers.Singleton(
        DatasetService,
        db=db.provided,
        dataset_repository=dataset_repository,
        workspace_repository=workspace_repository
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

    document_processor = providers.Singleton(
        LangchainDocumentProcessor
    )

    decryption_service = providers.Singleton(
        SimpleDocumentDecryptionService
    )

    chat_service = providers.Singleton(
        ChatService,
        llm_service=llm_service
    )

    llm_service = providers.Singleton(
        OpenAIService,
        settings=settings.provided.LLM,
    )

    # Transformers
    clean_transformer = providers.Singleton(
        ContentCleanTransformer
    )

    chunk_transformer = providers.Singleton(
        ChunkSplitTransformer,
        chunk_size=1000,
        chunk_overlap=200
    )

    faq_transformer = providers.Singleton(
        HypotheticalQuestionTransformer,
        llm=llm_service
    )

    summary_transformer = providers.Singleton(
        SummaryTransformer,
        llm=llm_service
    )

    # Embedding Service (按需创建)
    embedding_service = providers.Selector(
        settings.provided.EMBEDDING.PROVIDER,
        openai=providers.Singleton(
            OpenAIEmbeddingService,
            settings=settings.provided.EMBEDDING
        ),
        huggingface=providers.Singleton(
            HuggingFaceEmbeddingService,
            settings=settings.provided.EMBEDDING
        ),
        ollama=providers.Singleton(
            OpenAIEmbeddingService,
            settings=settings.provided.EMBEDDING
        )
    )

    openai_embedding = providers.Singleton(
        OpenAIEmbeddings,
        model=settings.provided.EMBEDDING.OPENAI_MODEL,
        openai_api_base=settings.provided.EMBEDDING.OPENAI_API_BASE,
        openai_api_key=settings.provided.EMBEDDING.OPENAI_API_KEY,
    )
    ollama_embedding = providers.Singleton(
        OllamaEmbeddings,
        model=settings.provided.EMBEDDING.OLLAMA_MODEL,
    )

    # Vector Store Service (按需创建)
    vector_store = providers.Selector(
        settings.provided.VECTOR_STORE.PROVIDER,
        chroma=providers.Singleton(
            ChromaVectorStore,
            embedding_service=embedding_service,
            settings=settings.provided.VECTOR_STORE
        ),
        milvus=providers.Singleton(
            MilvusVectorStore,
            embedding_service=embedding_service,
            settings=settings.provided.VECTOR_STORE
        ),
        opensearch=providers.Singleton(
            OpenSearchVectorStore,
            embedding_service=embedding_service,
            settings=settings.provided.VECTOR_STORE,
        )
    )

    document_store = providers.Selector(
        settings.provided.DOCUMENT_STORE.PROVIDER,
        mysql=providers.Singleton(
            MySQLDocumentStore,
            settings=settings.provided.DOCUMENT_STORE
        )
    )

    # Document Processing Activities
    load_document_activity = providers.Singleton(
        LoadDocumentActivity,
        storage_service=storage_service,
        resource_repository=resource_repository,
        document_processor=document_processor
    )

    clean_content_activity = providers.Singleton(
        CleanContentActivity,
        transformer=clean_transformer
    )

    split_documents_activity = providers.Singleton(
        SplitDocumentsActivity,
        transformer=chunk_transformer
    )

    store_documents_activity = providers.Singleton(
        StoreDocumentsActivity,
        doc_store=document_store,
    )

    hypothetical_question_activity = providers.Singleton(
        HypotheticalQuestionActivity,
        transformer=faq_transformer
    )

    generate_summary_activity = providers.Singleton(
        GenerateSummaryActivity,
        transformer=summary_transformer
    )

    vector_store_activity = providers.Singleton(
        VectorStoreActivity,
        embedding_service=ollama_embedding,
        vector_store_settings=settings.provided.VECTOR_STORE,
    )

    retrieve_activity = providers.Singleton(
        RetrieveActivity,
        doc_store=document_store,
        embedding_service=ollama_embedding,
        vector_store_settings=settings.provided.VECTOR_STORE,
    )
