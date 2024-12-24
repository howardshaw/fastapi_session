from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Type, Callable, Dict, Any, Union
from logging import getLogger

logger = getLogger(__name__)

# Base Exception
class AppException(Exception):
    """Base exception for application"""
    status_code = 500
    detail = "Internal Server Error"

    def __init__(self, detail: str = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


# Business Exceptions
class OrderCreationError(AppException):
    """Raised when order creation fails"""
    status_code = 400
    detail = "Order creation failed"


class DatabaseError(AppException):
    """Raised when database operations fail"""
    status_code = 500
    detail = "Database operation failed"


class InsufficientFundsError(AppException):
    """Raised when account has insufficient funds"""
    status_code = 400
    detail = "Insufficient funds"

    def __init__(self, account_id: int, required: float, available: float):
        self.account_id = account_id
        self.required = required
        self.available = available
        detail = f"Insufficient funds in account {account_id}: required {required}, available {available}"
        super().__init__(detail)


class AccountLockedError(AppException):
    """Raised when account is locked"""
    status_code = 403
    detail = "Account is locked"

    def __init__(self, account_id: int):
        self.account_id = account_id
        detail = f"Account {account_id} is locked"
        super().__init__(detail)


class AccountNotFoundError(AppException):
    """Raised when account is not found"""
    status_code = 404
    detail = "Account not found"

    def __init__(self, account_id: int):
        self.account_id = account_id
        detail = f"Account {account_id} not found"
        super().__init__(detail)


class TransferError(AppException):
    """Raised when transfer operation fails"""
    status_code = 400
    detail = "Transfer failed"

    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppException):
    """Raised when validation fails"""
    status_code = 422
    detail = "Validation error"


# Exception Handlers
def create_exception_handler(exc_class: Type[AppException]) -> Callable:
    """Factory function to create exception handlers"""
    async def handler(request: Request, exc: AppException) -> JSONResponse:
        error_msg = str(exc)
        logger.error(
            f"{exc_class.__name__}: {error_msg}",
            exc_info=exc,
            extra={
                "request_path": request.url.path,
                "request_method": request.method,
            }
        )
        
        # 构建响应内容
        content = {
            "error": exc_class.__name__,
            "message": error_msg,
            "status_code": exc.status_code
        }
        
        # 如果异常包含额外详情，添加到响应中
        if hasattr(exc, 'details'):
            content["details"] = exc.details
        
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    return handler


# Default exception handler for unhandled exceptions
async def default_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_msg = str(exc)
    logger.error(
        f"Unhandled exception: {error_msg}",
        exc_info=exc,
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "status_code": 500
        }
    )


# HTTP exception handler
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.error(
        f"HTTP exception: {exc.detail}",
        exc_info=exc,
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "status_code": exc.status_code
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


def register_exception_handlers(app: Any) -> None:
    """Register all exception handlers to the FastAPI app"""
    # Register custom exception handlers
    for exc_class in AppException.__subclasses__():
        app.add_exception_handler(exc_class, create_exception_handler(exc_class))
    
    # Register default exception handlers
    app.add_exception_handler(Exception, default_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)