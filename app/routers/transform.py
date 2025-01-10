import uuid

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, HTTPException, Depends
from temporalio.client import Client
from temporalio.exceptions import TemporalError

from app.core.containers import Container
from app.logger import get_logger
from app.schemas.transfer import TransferRequest, TransferResponse
from app.settings import TemporalSettings
from app.workflows.transfer.workflows import TransferWorkflow

logger = get_logger(__name__)
router = APIRouter(
    prefix="/transform",
    tags=["transform"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=TransferResponse)
@inject
async def transfer(
        transfer_request: TransferRequest,
        client: Client = Depends(Provide[Container.temporal_client]),
        settings: TemporalSettings = Depends(Provide[Container.settings.provided.TEMPORAL]),
):
    try:
        # Start workflow with correct arguments
        workflow_id = str(uuid.uuid4())
        logger.info(f"Starting transfer workflow: {workflow_id}")

        handle = await client.start_workflow(
            TransferWorkflow.run,
            args=[transfer_request.from_account, transfer_request.to_account, transfer_request.amount],
            id=workflow_id,
            task_queue=settings.TRANSFER_QUEUE,
        )

        logger.info(f"Transfer initiated: {handle}")
        return TransferResponse(
            workflow_id=workflow_id,
            result={"status": "initiated"},
            status="pending"
        )
    except TemporalError as e:
        logger.error(f"Temporal workflow error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start transfer workflow: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during transfer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
