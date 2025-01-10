import uuid
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, ActivityError

with workflow.unsafe.imports_passed_through():
    from app.workflows.transfer.activities import AccountActivities

@workflow.defn
class TransferWorkflow:
    """
    Transfer workflow implementation
    """
    @workflow.run
    async def run(self, from_account_id: uuid.UUID, to_account_id: uuid.UUID, amount: float) -> dict:
        """
        Execute transfer between accounts
        
        Args:
            from_account_id: Source account ID
            to_account_id: Target account ID
            amount: Amount to transfer
            
        Returns:
            dict: Transfer result with status and details
        """
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=5,
            non_retryable_error_types=["BusinessError"]
        )

        try:
            # Execute transfer activity
            await workflow.execute_activity(
                AccountActivities.transform_activity,
                args=[from_account_id, to_account_id, amount],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry_policy,
            )

            workflow.logger.info(
                f"Transfer completed: {amount} from {from_account_id} to {to_account_id}"
            )

            return {
                "status": "completed",
                "from_account": from_account_id,
                "to_account": to_account_id,
                "amount": amount
            }

        except ActivityError as e:
            workflow.logger.error(f"Activity error in transfer: {e}")

            if isinstance(e.cause, ApplicationError) and e.cause.details:
                error_details = e.cause.details
                workflow.logger.error(f"Error details: {error_details}")

                # if isinstance(error_details, list) and len(error_details) > 0:
                error_type, error_message = error_details[0]
                return {
                    "status": "failed",
                    "error": error_type.lower().replace("error", ""),
                    "message": error_message
                }

            return {
                "status": "failed",
                "error": "activity_error",
                "message": str(e.cause),
            }

        except Exception as e:
            workflow.logger.error(f"Unexpected error in transfer: {e}")
            return {
                "status": "failed",
                "error": "unexpected_error",
                "message": str(e)
            }
