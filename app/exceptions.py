from fastapi import HTTPException

class OrderCreationError(HTTPException):
    def __init__(self, detail: str = "Order creation failed"):
        super().__init__(status_code=400, detail=detail)

class DatabaseError(HTTPException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=500, detail=detail) 