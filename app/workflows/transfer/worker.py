import asyncio
import logging
import sys

from dependency_injector.wiring import inject, Provide
from temporalio.client import Client
from temporalio.worker import Worker

from app.core.containers import Container
from app.workflows.transfer.activities import AccountActivities
from app.workflows.transfer.workflows import TransferWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@inject
async def create_worker(
        client: Client = Provide[Container.temporal_client],
        activities: AccountActivities = Provide[Container.account_activities]
) -> Worker:
    """Create and configure a Temporal worker"""
    # Register workflow and activities

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
    """Worker entry point"""
    try:
        container = Container()
        container.wire(modules=[__name__])

        logger.info("Starting worker...")
        async with await create_worker() as worker:
            logger.info(f"Worker started on queue: {worker.task_queue}")
            await asyncio.Event().wait()

    except Exception as e:
        logger.error("Failed to start worker", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
