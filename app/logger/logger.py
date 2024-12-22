import logging
from logging.handlers import RotatingFileHandler
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
    # 配置日志轮换
    rotating_handler = RotatingFileHandler(
        filename="app.log",  # 日志文件名
        maxBytes=10 * 1024 * 1024,  # 每个日志文件的最大大小（10MB）
        backupCount=5,  # 最多保留的日志文件数量
        encoding="utf-8"  # 文件编码
    )

    # 配置日志格式
    logging.basicConfig(
        handlers=[rotating_handler],
        level=logging.INFO,
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
            raise ValueError(f"Unknown logging format: {format}")

    structlog.configure(
        # logger_factory=RichPrintLoggerFactory(),
        logger_factory=LoggerFactory(),
        processors=shared_processors + output_processors,
        context_class=threadlocal.wrap_dict(dict),
        # wrapper_class=structlog.make_filtering_bound_logger(
        #     logging.getLevelName(settings.LOG_LEVEL)
        # ),
        cache_logger_on_first_use=True,
    )
