import logging

from temporalio.client import Client
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class TemporalClientFactory:
    """Factory for creating Temporal Client instances"""

    @staticmethod
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def create(url) -> Client:
        """
        Create and configure a Temporal Client instance
        
        Returns:
            Client: Configured Temporal Client instance
        """
        logger.info(f"Connecting to temporal: {url}")
        client = await Client.connect(url)
        logger.info("Successfully connected to Temporal")
        return client
