import asyncio
import logging
import sys

from dependency_injector.wiring import inject, Provide
from temporalio.client import Client
from temporalio.worker import Worker

from app.activities import AccountActivities
from app.containers import Container
from app.workflows import TransferWorkflow

logger = logging.getLogger(__name__)


@inject
async def create_worker(
        client: Client = Provide[Container.temporal_client],
        activities: AccountActivities = Provide[Container.account_activities]
) -> Worker:
    """
    Create a Temporal worker with the specified client and activities
    """
    return Worker(
        client,
        task_queue="transfer-task-queue",
        workflows=[TransferWorkflow],
        activities=[
            activities.withdraw_activity,
            activities.deposit_activity,
            activities.transform_activity,
        ],
    )


async def main():
    """
    Main entry point for the worker when run as a standalone script
    """
    try:
        # Initialize DI container
        container = Container()
        
        # Only wire if running as standalone script
        if __name__ == "__main__":
            container.wire(modules=[__name__])
        
        # Create and start worker
        async with await create_worker() as worker:
            logger.info("Worker started. Waiting for tasks...")
            # Wait indefinitely
            await asyncio.Event().wait()
            
    except Exception as e:
        logger.error(f"Worker failed to start: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
