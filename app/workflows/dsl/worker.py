import asyncio
import sys

from dependency_injector.wiring import inject, Provide
from temporalio.client import Client
from temporalio.worker import Worker

from app.core.containers import Container
from app.logger import get_logger, setup_logging
from app.workflows.dsl.activities import DSLActivities
from app.workflows.dsl.workflows import DSLWorkflow

logger = get_logger(__name__)


@inject
async def create_worker(
        client: Client = Provide[Container.temporal_client],
        activities: DSLActivities = Provide[Container.dsl_activities]
) -> Worker:
    """Create and configure a Temporal worker"""
    # Register workflow and activities

    return Worker(
        client,
        task_queue="dsl-task-queue",
        activities=[
            activities.activity1,
            activities.activity2,
            activities.activity3,
            activities.activity4,
            activities.activity5,
        ],
        workflows=[DSLWorkflow],
    )


async def main():
    """Worker entry point"""
    try:
        container = Container()
        container.wire(modules=[__name__])
        settings = container.settings()
        setup_logging(settings)

        logger.info("Starting worker...")
        async with await create_worker() as worker:
            logger.info(f"Worker started on queue: {worker.task_queue}")
            await asyncio.Event().wait()

    except Exception as e:
        logger.error("Failed to start worker", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
