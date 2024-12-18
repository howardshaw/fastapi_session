from fastapi import HTTPException


class OrderCreationError(HTTPException):
    def __init__(self, detail: str = "Order creation failed"):
        super().__init__(status_code=400, detail=detail)


class DatabaseError(HTTPException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=500, detail=detail)


class InsufficientFundsError(Exception):
    def __init__(self, account_id: int, required: float, available: float):
        self.account_id = account_id
        self.required = required
        self.available = available
        message = f"Insufficient funds in account {account_id}: required {required}, available {available}"
        super().__init__(message)


class AccountLockedError(Exception):
    def __init__(self, account_id: int):
        self.account_id = account_id
        message = f"Account {account_id} locked"
        super().__init__(message)


class AccountNotFoundError(Exception):
    def __init__(self, account_id: int):
        self.account_id = account_id
        message = f"Account {account_id} not found"
        super().__init__(message)


class TransferError(Exception):
    def __init__(self, message: str, details: dict | None = None):
        self.details = details or {}
        super().__init__(message)