from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.containers import Container
from app.exceptions import OrderCreationError
from app.logger import logger
from app.models import Base
from app.routers import transactions, users, transform, translate

# 初始化容器
container = Container()


async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 获取日志实例
# logger = container.logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 打印容器提供者信息
    logger.info("=== Container Providers ===")
    for provider_name, provider in container.providers.items():
        provider_type = type(provider).__name__
        logger.info(f"Provider: {provider_name}, Type: {provider_type}")
    logger.info("========================")

    # 初始化数据库
    database = container.db()
    await database.init_db()
    logger.info("Database initialized")

    try:
        yield
    finally:
        # Container 会自动管理资源的清理
        container.shutdown_resources()
        logger.info("Resources cleaned up")


app = FastAPI(lifespan=lifespan)
app.container = container

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(transform.router, prefix="/transform", tags=["transform"])
app.include_router(translate.router, prefix="/translate", tags=["translate"])


# 配置异常处理
@app.exception_handler(OrderCreationError)
async def order_creation_error_handler(request: Request, exc: OrderCreationError):
    logger.error(f"Order creation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
