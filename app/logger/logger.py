import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog
from opentelemetry import trace
from structlog import threadlocal
from structlog.dev import ConsoleRenderer
from structlog.processors import ExceptionRenderer, ExceptionDictTransformer
from structlog.stdlib import LoggerFactory

from app.settings import Settings

LoggerType = structlog.BoundLoggerBase


def inject_trace_id(logger: LoggerType, method_name: str, event_dict: dict) -> dict:
    """注入 trace_id 到日志中。

    如果当前上下文中有有效的 trace_id，则注入到日志中。
    如果没有有效的 trace_id（比如不在请求上下文中），则跳过注入。
    """
    if not event_dict.get("trace_id"):
        try:
            current_span = trace.get_current_span()
            if current_span:
                span_context = current_span.get_span_context()
                if span_context and span_context.is_valid and span_context.trace_id != 0:
                    event_dict["trace_id"] = trace.format_trace_id(span_context.trace_id)
        except Exception:
            # 如果获取 trace_id 失败，我们不希望影响日志记录
            pass
    return event_dict


def get_logger(name: str, **kwargs) -> Any:
    return structlog.get_logger(name, **kwargs)


def setup_logging(
        settings: Settings,
) -> None:
    """设置日志配置

    Args:
        settings: 应用配置对象

    配置说明：
        - 日志文件位置：由 settings.LOG_FILE_PATH 指定
        - 日志轮转：
            - 单个文件最大大小：由 settings.LOG_FILE_MAX_BYTES 指定（默认10MB）
            - 保留文件数：由 settings.LOG_FILE_BACKUP_COUNT 指定（默认5个）
            - 使用 UTF-8 编码
        - 支持两种输出格式：
            - CONSOLE：彩色控制台输出
            - JSON：结构化 JSON 输出
    """
    # 创建日志目录
    log_path = Path(settings.LOG_FILE_PATH)
    log_dir = log_path.parent
    log_dir.mkdir(exist_ok=True)

    # 配置日志轮转
    rotating_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding="utf-8"
    )

    # 配置日志格式
    logging.basicConfig(
        handlers=[rotating_handler],
        level=settings.LOG_LEVEL,
    )

    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.INCLUDE_TRACE_ID:
        shared_processors.append(inject_trace_id)

    match settings.LOG_FORMAT.upper():
        case "CONSOLE":
            output_processors = [
                ConsoleRenderer(colors=settings.LOG_COLORS),
            ]
        case "JSON":
            output_processors = [
                ExceptionRenderer(
                    ExceptionDictTransformer(
                        show_locals=settings.TRACEBACK_SHOW_LOCALS,
                        locals_max_string=100,
                        max_frames=settings.TRACEBACK_MAX_FRAMES,
                    )
                ),
                structlog.processors.JSONRenderer()
            ]
        case _:
            raise ValueError(f"Unknown logging format: {settings.LOG_FORMAT}")

    structlog.configure(
        logger_factory=LoggerFactory(),
        processors=shared_processors + output_processors,
        context_class=threadlocal.wrap_dict(dict),
        cache_logger_on_first_use=True,
    )
