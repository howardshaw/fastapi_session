from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.containers import Container
from app.routers import transactions, users
from app.containers import init_db
from app.exceptions import OrderCreationError, DatabaseError

# 初始化依赖注入容器
container = Container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n=== Container Providers ===")
    for provider_name, provider in container.providers.items():
        provider_type = type(provider).__name__
        print(f"Provider: {provider_name}, Type: {provider_type}")
    print("========================\n")
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.container = container

# 注册路由
app.include_router(transactions.router, prefix="/transactions")
app.include_router(users.router, prefix="/users")

@app.exception_handler(OrderCreationError)
async def order_creation_error_handler(request: Request, exc: OrderCreationError):
    # 打印预期的业务异常和调用栈
    import traceback
    print(f"Business error occurred: {exc}")
    print("Traceback:")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # 打印未预期的异常和完整调用栈
    import traceback
    print(f"Unexpected error occurred: {exc}")
    print("Traceback:")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
