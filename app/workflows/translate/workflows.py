from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.workflows.translate.activities import TranslateParams, TranslateActivities
    from typing import Dict


@workflow.defn
class TranslateWorkflow:
    @workflow.run
    async def run(self, params: TranslateParams, task_id: str) -> Dict[str, str]:
        workflow.logger.info(f"workflow run_id: {workflow.info().run_id}, task_id: {task_id}")
        result = await workflow.execute_activity(
            TranslateActivities.translate_phrase,
            args=[params, task_id],
            schedule_to_close_timeout=timedelta(seconds=30),
        )
        workflow.logger.info("activity translate_phrase done")
        await workflow.execute_activity(
            TranslateActivities.complete_translate,
            task_id,
            schedule_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info("workflow done")
        return {
            "result": result,
        }
