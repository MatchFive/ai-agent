"""
记忆/上下文管理模块
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from .logger import logger


class MemoryItem(BaseModel):
    """单条记忆"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseMemory(ABC):
    """记忆存储基类"""

    @abstractmethod
    async def add(self, item: MemoryItem) -> None:
        """添加记忆"""
        pass

    @abstractmethod
    async def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        pass

    @abstractmethod
    async def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """获取最近n条记忆"""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """清空记忆"""
        pass


class InMemoryStorage(BaseMemory):
    """内存存储实现"""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._storage: List[MemoryItem] = []

    async def add(self, item: MemoryItem) -> None:
        """添加记忆，超过最大容量时删除最旧的"""
        if len(self._storage) >= self.max_size:
            self._storage.pop(0)
        self._storage.append(item)
        logger.debug(f"Added memory item: {item.role}")

    async def get_all(self) -> List[MemoryItem]:
        """获取所有记忆"""
        return self._storage.copy()

    async def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """获取最近n条记忆"""
        return self._storage[-n:] if n > 0 else []

    async def clear(self) -> None:
        """清空记忆"""
        self._storage.clear()
        logger.info("Memory cleared")


class Memory:
    """
    记忆管理器
    管理对话历史和上下文
    """

    def __init__(
        self,
        storage: Optional[BaseMemory] = None,
        max_context_tokens: int = 4000,
        system_prompt: Optional[str] = None,
    ):
        self.storage = storage or InMemoryStorage()
        self.max_context_tokens = max_context_tokens
        self.system_prompt = system_prompt

    async def add_user_message(self, content: str, **metadata) -> None:
        """添加用户消息"""
        await self.storage.add(MemoryItem(
            role="user",
            content=content,
            metadata=metadata
        ))

    async def add_assistant_message(self, content: str, **metadata) -> None:
        """添加助手消息"""
        await self.storage.add(MemoryItem(
            role="assistant",
            content=content,
            metadata=metadata
        ))

    async def add_system_message(self, content: str, **metadata) -> None:
        """添加系统消息"""
        await self.storage.add(MemoryItem(
            role="system",
            content=content,
            metadata=metadata
        ))

    async def get_context(
        self,
        include_system: bool = True,
        max_items: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        获取对话上下文

        Args:
            include_system: 是否包含系统消息
            max_items: 最大消息数量

        Returns:
            格式化的消息列表
        """
        items = await self.storage.get_recent(max_items) if max_items else await self.storage.get_all()

        context = []

        # 添加系统提示
        if include_system and self.system_prompt:
            context.append({"role": "system", "content": self.system_prompt})

        # 添加历史消息
        for item in items:
            if item.role != "system":  # 系统消息单独处理
                context.append({"role": item.role, "content": item.content})

        return context

    async def clear(self) -> None:
        """清空记忆"""
        await self.storage.clear()

    async def get_history_summary(self) -> str:
        """获取历史摘要"""
        items = await self.storage.get_all()
        if not items:
            return "No conversation history."

        summary_parts = []
        for item in items[-10:]:  # 最近10条
            role_name = item.role.capitalize()
            content_preview = item.content[:100] + "..." if len(item.content) > 100 else item.content
            summary_parts.append(f"{role_name}: {content_preview}")

        return "\n".join(summary_parts)
