import asyncio

from dependency_injector.wiring import inject, Provide
from temporalio.client import Client
from temporalio.worker import Worker

from app.core.containers import Container
from app.logger import get_logger, setup_logging
from app.settings import TemporalSettings
from app.workflows.dsl.activities import (
    LoadDocumentActivity,
    SplitDocumentsActivity,
    StoreDocumentsActivity,
    TransformDocumentsActivity,
    VectorStoreActivity,
    RetrieveActivity,
)
from app.workflows.dsl.workflows import DSLWorkflow
from app.workflows.runner.sandbox import new_sandbox_runner

logger = get_logger(__name__)


@inject
async def create_worker(
        settings: TemporalSettings = Provide[Container.settings.provided.TEMPORAL],
        client: Client = Provide[Container.temporal_client],
        load_document_activity: LoadDocumentActivity = Provide[Container.load_document_activity],
        split_documents_activity: SplitDocumentsActivity = Provide[Container.split_documents_activity],
        store_documents_activity: StoreDocumentsActivity = Provide[Container.store_documents_activity],
        transform_activity: TransformDocumentsActivity = Provide[
            Container.transform_activity],
        vector_store_activity: VectorStoreActivity = Provide[Container.vector_store_activity],
        retrieve_activity: RetrieveActivity = Provide[Container.retrieve_activity],
) -> Worker:
    """Create and configure a Temporal worker"""
    return Worker(
        client,
        task_queue=settings.DSL_QUEUE,
        activities=[
            load_document_activity.run,
            split_documents_activity.run,
            store_documents_activity.run,
            transform_activity.run,
            vector_store_activity.run,
            retrieve_activity.run,
        ],
        workflows=[DSLWorkflow],
        max_cached_workflows=1000,
        max_concurrent_workflow_tasks=100,
        max_concurrent_activities=100,
        max_concurrent_local_activities=100,
        max_concurrent_workflow_task_polls=10,
        max_concurrent_activity_task_polls=10,
        workflow_runner=new_sandbox_runner(),
    )


async def main():
    """Worker entry point"""

    container = Container()
    container.wire(modules=[__name__])
    settings = container.settings()
    setup_logging(settings)

    logger.info("Starting worker...")
    async with await create_worker() as worker:
        logger.info(f"Worker started on queue: {worker.task_queue}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
