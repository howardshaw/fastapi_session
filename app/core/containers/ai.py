from dependency_injector import containers, providers
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.services.embeddings import (
    OpenAIEmbeddingService,
    HuggingFaceEmbeddingService,
    OllamaEmbeddingService,
)
from app.services.llm import (
    ClaudeService,
    OllamaService,
    OpenAIService,
)
from app.services.vector_store import (
    ChromaVectorStore,
    MilvusVectorStore,
    OpenSearchVectorStore,
)
from app.settings import Settings


class AIContainer(containers.DeclarativeContainer):
    """AI related dependencies container (LLM, Embeddings, Vector Store)."""

    settings = providers.Dependency(instance_of=Settings)

    # LLM
    llm = providers.Factory(
        ChatOpenAI,
        api_key=settings.provided.LLM.OPENAI_API_KEY,
        base_url=settings.provided.LLM.OPENAI_BASE_URL,
        model=settings.provided.LLM.OPENAI_MODEL,
    )

    # EMBEDDING
    embedding = providers.Factory(
        OpenAIEmbeddings,
        api_key=settings.provided.EMBEDDING.OPENAI_API_KEY,
        base_url=settings.provided.EMBEDDING.OPENAI_BASE_URL,
        model=settings.provided.EMBEDDING.OPENAI_MODEL,
    )

    # LLM Service
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

    # Embeddings Service
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
            OllamaEmbeddingService,
            settings=settings.provided.EMBEDDING
        )
    )

    # Vector Store Service
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
