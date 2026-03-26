"""
时间工具
获取当前服务器时间，避免模型时间幻觉
"""

from datetime import datetime, timezone
from typing import Dict, Any

from loguru import logger

tool_logger = logger.bind(category="tool")


class TimeTool:
    """时间查询工具"""

    def get_current_time(self) -> Dict[str, Any]:
        """
        获取当前服务器时间

        Returns:
            {
                "success": True,
                "datetime": "2026-03-26 22:30:00",
                "date": "2026-03-26",
                "time": "22:30:00",
                "weekday": "星期四",
                "timestamp": 1742997000,
                "timezone": "Asia/Shanghai"
            }
        """
        now = datetime.now(timezone.utc).astimezone()

        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

        result = {
            "success": True,
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": weekdays[now.weekday()],
            "timestamp": int(now.timestamp()),
            "timezone": str(now.tzinfo),
        }

        tool_logger.info(f"[时间工具] 当前时间 | {result['datetime']} {result['weekday']}")
        return result
