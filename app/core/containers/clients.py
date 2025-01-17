from dependency_injector import containers, providers
from redis.asyncio import Redis

from app.core.clients import TemporalClientFactory
from app.settings import Settings


class ClientsContainer(containers.DeclarativeContainer):
    """Clients dependencies container."""

    settings = providers.Dependency(instance_of=Settings)

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
