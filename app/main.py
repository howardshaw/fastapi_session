import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import prometheus_client
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.containers import Container
from app.exceptions import OrderCreationError
from app.logger import logger
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, REGISTRY
from app.routers import users, transactions, translate, transform

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        path = request.url.path

        # 记录请求开始时间
        with REQUEST_LATENCY.labels(method=method, endpoint=path).time():
            response = await call_next(request)

        # 记录请求计数
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            http_status=response.status_code
        ).inc()

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动前的初始化
    container = Container()

    # 初始化数据库
    db = container.db()
    await db.init_db()
    logger.info("Database initialized")

    # 设置 prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(
            prometheus_client.generate_latest(REGISTRY),
            media_type="text/plain"
        )

    yield

    # 清理资源
    await container.shutdown_resources()
    logger.info("Resources cleaned up")


app = FastAPI(lifespan=lifespan)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加 metrics 中间件
app.add_middleware(MetricsMiddleware)

# 注册路由
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(translate.router, prefix="/translate", tags=["translate"])
app.include_router(transform.router, prefix="/transform", tags=["transform"])


# 配置异常处理
@app.exception_handler(OrderCreationError)
async def order_creation_error_handler(request: Request, exc: OrderCreationError):
    logger.error(f"Order creation error: {exc}")
    return Response(
        status_code=400,
        content={"message": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return Response(
        status_code=500,
        content={"message": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
