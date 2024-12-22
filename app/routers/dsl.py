import uuid
from typing import Dict, Any

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends
from temporalio.client import Client

from app.core.containers import Container
from app.logger.logger import get_logger
from app.schemas.dsl import DSLRequest
from app.settings import Settings
from app.workflows.dsl.workflows import DSLWorkflow, DSLInput, ActivityStatement, ActivityInvocation, \
    SequenceStatement, Sequence, ParallelStatement, Parallel

router = APIRouter()
logger = get_logger(__name__)


def convert_to_dsl_input(request: DSLRequest) -> DSLInput:
    """将 DSLRequest 转换为 DSLInput"""

    def convert_activity(act_def: Dict[str, Any]) -> ActivityStatement:
        return ActivityStatement(
            activity=ActivityInvocation(
                name=act_def["name"],
                arguments=act_def["arguments"],
                result=act_def["result"]
            )
        )

    def convert_sequence(seq_def: Dict[str, Any]) -> SequenceStatement:
        elements = []
        for elem in seq_def["elements"]:
            if "activity" in elem:
                elements.append(convert_activity(elem["activity"]))
            elif "parallel" in elem:
                elements.append(convert_parallel(elem["parallel"]))
        return SequenceStatement(sequence=Sequence(elements=elements))

    def convert_parallel(par_def: Dict[str, Any]) -> ParallelStatement:
        branches = []
        for branch in par_def["branches"]:
            if "sequence" in branch:
                branches.append(convert_sequence(branch["sequence"]))
        return ParallelStatement(parallel=Parallel(branches=branches))

    # 转换根节点
    root_statement = convert_sequence(request.root.sequence.dict())

    return DSLInput(
        root=root_statement,
        variables=request.variables
    )


@router.post("/")
@inject
async def create_dsl_workflow(
        dsl_request: DSLRequest,
        client: Client = Depends(Provide[Container.temporal_client]),
        settings: Settings = Depends(Provide[Container.settings]),
):
    logger.info(f"dsl request: {dsl_request}")
    dsl_input = convert_to_dsl_input(dsl_request)

    task_id = str(uuid.uuid4())
    result = await client.execute_workflow(
        DSLWorkflow.run,
        dsl_input,
        id=f"dsl-{task_id}",
        task_queue=settings.TEMPORAL_DSL_QUEUE,
    )
    return result
