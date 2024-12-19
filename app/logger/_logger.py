"""Loggers to override default FastAPI uvicorn logger behavior."""

import os
import sys

from loguru import logger as base_logger


def setup_logger(log_level: str = None) -> None:
    """
    Setup global logger configuration
    """
    try:
        base_logger.remove(0)
    except ValueError:
        pass

    base_logger.add(
        sink=sys.stderr,
        colorize=True,
        level=log_level or os.environ.get("LOG_LEVEL", "INFO"),
        format="<fg #808080>{time:YYYY-MM-DD HH:mm:ss.SSSSSS}Z [{process}] |</fg #808080>"
        " <level>{level: <8}  <fg #808080>{name}:{function}:{line} -</fg #808080> {message}"
        " <fg #808080>|</fg #808080> {extra}</level>",
    )


# 初始化全局logger配置
setup_logger()

# 导出全局logger实例
logger = base_logger
