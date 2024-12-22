import json
import uuid

import redis.asyncio as redis
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from temporalio.client import Client

from app.core.containers import Container
from app.core.queue_manager import QueueManager
from app.logger.logger import get_logger
from app.schemas.translate import TranslateRequest
from app.settings import Settings
from app.workflows.translate.activities import TranslateParams
from app.workflows.translate.workflows import TranslateWorkflow

router = APIRouter()

logger = get_logger(__name__)


@router.post("/")
@inject
async def translate(
        translate_request: TranslateRequest,
        client: Client = Depends(Provide[Container.temporal_client]),
        redis_client: redis.Redis = Depends(Provide[Container.redis_client]),
        settings: Settings = Depends(Provide[Container.settings]),
):
    logger.info(f"translate request: {translate_request}")
    async def event_generator():
        try:
            task_id = str(uuid.uuid4())
            queue_manager = QueueManager(redis_client=redis_client, task_id=task_id)
            await client.start_workflow(
                TranslateWorkflow.run,
                args=[TranslateParams(translate_request.phase, translate_request.language), task_id],
                id=task_id,
                task_queue=settings.TEMPORAL_TRANSLATE_QUEUE,
            )

            async for message in queue_manager.listen():
                yield f"data: {json.dumps(message)}\n\n"

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
