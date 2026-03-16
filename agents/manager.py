"""
Agent管理器
负责注册、发现和调度Agent
"""

from typing import Dict, List, Optional, Type
from core.logger import logger
from .base import BaseAgent


class AgentManager:
    """
    Agent管理器
    单例模式，管理所有Agent实例
    """

    _instance: Optional['AgentManager'] = None
    _agents: Dict[str, BaseAgent] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'AgentManager':
        """获取管理器实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, agent: BaseAgent) -> None:
        """
        注册Agent

        Args:
            agent: Agent实例
        """
        if agent.name in self._agents:
            logger.warning(f"Agent '{agent.name}' already exists, overwriting")

        self._agents[agent.name] = agent
        logger.info(f"Agent '{agent.name}' registered")

    def unregister(self, name: str) -> bool:
        """
        注销Agent

        Args:
            name: Agent名称

        Returns:
            是否成功
        """
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Agent '{name}' unregistered")
            return True
        return False

    def get(self, name: str) -> Optional[BaseAgent]:
        """
        获取Agent

        Args:
            name: Agent名称

        Returns:
            Agent实例或None
        """
        return self._agents.get(name)

    def list_agents(self) -> List[Dict[str, str]]:
        """列出所有已注册的Agent"""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "status": agent.status.value,
            }
            for agent in self._agents.values()
        ]

    def get_all(self) -> Dict[str, BaseAgent]:
        """获取所有Agent"""
        return self._agents.copy()

    async def dispatch(
        self,
        agent_name: str,
        message: str,
        **kwargs
    ) -> str:
        """
        调度消息到指定Agent

        Args:
            agent_name: Agent名称
            message: 消息内容
            **kwargs: 额外参数

        Returns:
            Agent响应
        """
        agent = self.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        return await agent.run(message, **kwargs)

    async def broadcast(self, message: str, **kwargs) -> Dict[str, str]:
        """
        广播消息到所有Agent

        Args:
            message: 消息内容
            **kwargs: 额外参数

        Returns:
            各Agent的响应
        """
        results = {}
        for name, agent in self._agents.items():
            try:
                results[name] = await agent.run(message, **kwargs)
            except Exception as e:
                results[name] = f"Error: {e}"
                logger.error(f"Broadcast to '{name}' failed: {e}")

        return results

    def clear(self) -> None:
        """清空所有Agent"""
        self._agents.clear()
        logger.info("All agents cleared")


# 全局管理器实例
agent_manager = AgentManager.get_instance()
