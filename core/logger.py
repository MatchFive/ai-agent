"""
日志系统模块
"""

import sys
from pathlib import Path

from loguru import logger

# 移除默认handler
logger.remove()

# 控制台输出格式
console_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 文件输出格式
file_format = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} | "
    "{message}"
)


def setup_logger(
    log_level: str = "INFO",
    log_dir: str = "logs",
    rotation: str = "10 MB",
    retention: str = "7 days",
):
    """
    配置日志系统

    Args:
        log_level: 日志级别
        log_dir: 日志目录
        rotation: 日志轮转大小
        retention: 日志保留时间
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 添加控制台handler
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        enqueue=True,
    )

    # 添加文件handler - 所有日志
    logger.add(
        log_path / "agent_{time:YYYY-MM-DD}.log",
        format=file_format,
        level=log_level,
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
    )

    # 添加错误日志文件
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
    )

    # 工具调用专用日志文件
    logger.add(
        log_path / "tools_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="INFO",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("category") == "tool",
    )

    return logger


# 导出配置好的logger
logger = setup_logger()
