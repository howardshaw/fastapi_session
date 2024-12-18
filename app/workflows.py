from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError, ActivityError

with workflow.unsafe.imports_passed_through():
    from app.activities import AccountActivities


@workflow.defn
class TransferWorkflow:
    @workflow.run
    async def run(self, from_account_id: int, to_account_id: int, amount: float) -> dict:
        """
        执行账户转账的逻辑
        """
        try:
            await workflow.execute_activity(
                AccountActivities.transform_activity,
                args=[from_account_id, to_account_id, amount],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=5,  # 最多重试5次
                    non_retryable_error_types=[
                        "BusinessError"  # 业务错误不重试
                    ]
                )
            )
            return {
                "status": "completed",
                "from_account": from_account_id,
                "to_account": to_account_id,
                "amount": amount
            }
        except ActivityError as e:
            workflow.logger.error(f"TransferWorkflow failed: {e} {e.cause}")
            
            # 从 ActivityError 中提取业务错误信息
            if isinstance(e.cause, ApplicationError) and e.cause.details:
                error_details = e.cause.details
                workflow.logger.error(f"TransferWorkflow error details: {error_details}")
                
                # error_details[0] 是包含 [error_type, error_message] 的列表
                error_info = error_details[0]
                error_type, error_message = error_info
                
                return {
                    "status": "failed",
                    "error": error_type.lower().replace("error", ""),  # 转换错误类型为更友好的格式
                    "message": error_message
                }
            
            # 如果无法获取详细信息，返回通用错误
            return {
                "status": "failed",
                "error": "activity_error",
                "message": str(e.cause),
            }

        except Exception as e:
            workflow.logger.error(f"Unexpected error: {type(e)} {e}")
            return {
                "status": "failed",
                "error": "unexpected_error",
                "message": str(e)
            }
