"""
AI-Agent 多Agent集成框架
"""

__version__ = "0.1.0"

from .base import BaseAgent, AgentStatus, Tool, ToolResult
from .manager import AgentManager, agent_manager

__all__ = [
    # Base
    "BaseAgent",
    "AgentStatus",
    "Tool",
    "ToolResult",
    # Manager
    "AgentManager",
    "agent_manager",
]
