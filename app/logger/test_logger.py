"""
测试日志轮转功能
"""
import os
import time
from pathlib import Path

import structlog
from app.settings import Settings
from app.logger.logger import setup_logging

def generate_large_logs(logger: structlog.BoundLoggerBase, size_mb: int = 12):
    """
    生成大量日志以触发日志轮转
    :param logger: 日志记录器
    :param size_mb: 要生成的日志大小（MB）
    """
    # 生成一个1KB的日志消息
    message = "Test log message " * 50  # 约1KB

    # 计算需要写入的次数
    iterations = size_mb * 1024  # 每MB需要写入1024次1KB的消息

    for i in range(iterations):
        logger.info(
            "test_log_rotation",
            iteration=i,
            message=message,
            test_data="Some test data"
        )
        if i % 100 == 0:  # 每100次迭代打印进度
            print(f"Generated {i/iterations*100:.1f}% of logs")
        time.sleep(0.001)  # 小延迟，避免过快写入

def check_log_files():
    """
    检查生成的日志文件
    """
    log_dir = Path(".")
    log_files = sorted(log_dir.glob("app.log*"))
    
    print("\nLog files found:")
    for log_file in log_files:
        size_mb = os.path.getsize(log_file) / (1024 * 1024)
        print(f"{log_file.name}: {size_mb:.2f}MB")

def main():
    # 设置日志
    settings = Settings()
    setup_logging(settings)
    logger = structlog.get_logger("test_logger")

    # 记录初始状态
    print("Initial log files:")
    check_log_files()

    # 生成大量日志
    print("\nGenerating logs...")
    generate_large_logs(logger)

    # 记录最终状态
    print("\nFinal log files:")
    check_log_files()

if __name__ == "__main__":
    main()
