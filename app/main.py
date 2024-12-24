"""
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.containers import Container
from app.core.exceptions import register_exception_handlers
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.core.observability.logs import setup_telemetry_logging
from app.core.observability.metrics import setup_telemetry_metrics
from app.core.observability.tracings import (
    setup_telemetry_tracing,
    shutdown_telemetry,
    init_fastapi_instrumentation,
    instrument_threads
)
from app.logger.logger import get_logger, setup_logging
from app.routers import users, transactions, translate, transform, dsl, monitoring
from app.settings import settings


# 初始化日志
setup_logging(settings=settings)
logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """中间件：记录请求计数和延迟"""
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path = request.url.path
        
        # 记录请求延迟
        with REQUEST_LATENCY.labels(
            method=method,
            endpoint=path
        ).time():
            response = await call_next(request)
        
        # 记录请求计数
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            http_status=response.status_code
        ).inc()
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理
    - 启动时初始化：数据库、可观测性组件
    - 关闭时清理：关闭可观测性组件
    """
    # 初始化依赖注入容器
    container = Container()
    app.container = container
    settings = container.settings()
    
    # 初始化可观测性组件
    setup_telemetry_logging(settings)
    setup_telemetry_metrics(settings)
    setup_telemetry_tracing(settings)
    
    # 初始化数据库
    db = container.db()
    await db.init_db()
    logger.info("Database initialized")

    yield

    # 清理资源
    await shutdown_telemetry()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用
    """
    app = FastAPI(lifespan=lifespan)
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册中间件
    app.add_middleware(MetricsMiddleware)
    
    # 注册路由
    _register_routers(app)
    
    # 注册异常处理器
    register_exception_handlers(app)
    
    # 初始化可观测性
    init_fastapi_instrumentation(app)
    instrument_threads()
    
    return app


def _register_routers(app: FastAPI) -> None:
    """
    注册所有路由模块
    """
    app.include_router(users.router)
    app.include_router(transactions.router)
    app.include_router(translate.router)
    app.include_router(transform.router)
    app.include_router(dsl.router)
    app.include_router(monitoring.router)


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
