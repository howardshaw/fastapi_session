import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.containers import Container
from app.exceptions import OrderCreationError
from app.routers import transactions, users, transform
from app.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化依赖注入容器
container = Container()


async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 打印容器提供者信息
    print("\n=== Container Providers ===")
    for provider_name, provider in container.providers.items():
        provider_type = type(provider).__name__
        print(f"Provider: {provider_name}, Type: {provider_type}")
    print("========================\n")
    
    # 初始化数据库
    engine = container.engine()  # 获取实际的 engine 实例
    await init_db(engine)
    
    try:
        yield
    finally:
        # Container 会自动管理资源的清理
        await container.shutdown_resources()


app = FastAPI(lifespan=lifespan)
app.container = container

# 配置路由
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(transform.router, prefix="/transform", tags=["transform"])

# 配置异常处理
@app.exception_handler(OrderCreationError)
async def order_creation_error_handler(request: Request, exc: OrderCreationError):
    # 打印预期的业务异常和调用栈
    import traceback
    print(f"Business error occurred: {exc}")
    print("Traceback:")
    traceback.print_exc()
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    # 打印预期的业务异常和调用栈
    import traceback
    print(f"Business error occurred: {exc}")
    print("Traceback:")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
