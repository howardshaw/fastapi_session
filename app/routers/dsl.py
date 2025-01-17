import uuid

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from temporalio.client import Client

from app.core.containers import Container
from app.logger.logger import get_logger
from app.schemas.dsl import DSLRequest
from app.settings import TemporalSettings
from app.workflows.dsl.workflows import DSLWorkflow

router = APIRouter(
    prefix="/dsl",
    tags=["dsl"],
    responses={404: {"description": "Not found"}},
)
logger = get_logger(__name__)


@router.post("/workflows/dsl")
@inject
async def create_dsl_workflow(
        dsl_request: DSLRequest,
        client: Client = Depends(Provide[Container.clients.temporal_client]),
        settings: TemporalSettings = Depends(Provide[Container.settings.provided.TEMPORAL]),
):
    """创建并执行 DSL 工作流"""
    workflow_id = str(uuid.uuid4())

    # 转换请求为工作流输入
    dsl_input = dsl_request.to_dsl_input()

    # 启动工作流
    result = await client.execute_workflow(
        DSLWorkflow.run,
        dsl_input,
        id=workflow_id,
        task_queue=settings.DSL_QUEUE,
    )

    return {"workflow_id": workflow_id, "result": result}
