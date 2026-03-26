"""
对话数据模型
使用MySQL数据库持久化对话记录
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import Base, _async_session_factory
from core.memory import BaseMemory, MemoryItem
from core.logger import logger


class Conversation(Base):
    """对话表 - 以 conversation_id 为主键"""
    __tablename__ = "conversations"

    conversation_id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    messages = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Conversation(id='{self.conversation_id}', user_id={self.user_id})>"


class DatabaseStorage(BaseMemory):
    """基于数据库的对话存储"""

    def __init__(self, conversation_id: str, user_id: Optional[int] = None):
        self.conversation_id = conversation_id
        self.user_id = user_id

    async def _get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if _async_session_factory is None:
            raise RuntimeError("数据库未初始化，请先调用 init_db()")
        return _async_session_factory()

    async def _load_conversation(self, session: AsyncSession) -> Conversation:
        """加载或创建对话记录"""
        result = await session.execute(
            select(Conversation).where(
                Conversation.conversation_id == self.conversation_id
            )
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            conv = Conversation(
                conversation_id=self.conversation_id,
                user_id=self.user_id,
                messages="[]",
            )
            session.add(conv)
            await session.flush()
        return conv

    async def add(self, item: MemoryItem) -> None:
        """添加消息到对话"""
        async with await self._get_session() as session:
            conv = await self._load_conversation(session)

            # 解析现有消息
            try:
                messages = json.loads(conv.messages)
            except (json.JSONDecodeError, TypeError):
                messages = []

            # 追加新消息
            messages.append({
                "role": item.role,
                "content": item.content,
                "timestamp": item.timestamp.isoformat() if item.timestamp else datetime.utcnow().isoformat(),
            })

            conv.messages = json.dumps(messages, ensure_ascii=False)
            conv.updated_at = datetime.utcnow()
            await session.commit()

        logger.debug(f"[DBStorage] 消息已保存 | conversation={self.conversation_id} | role={item.role}")

    async def get_all(self) -> List[MemoryItem]:
        """获取所有消息"""
        async with await self._get_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.conversation_id == self.conversation_id
                )
            )
            conv = result.scalar_one_or_none()
            if not conv:
                return []

            try:
                messages = json.loads(conv.messages)
            except (json.JSONDecodeError, TypeError):
                return []

            return [
                MemoryItem(
                    role=m["role"],
                    content=m["content"],
                    timestamp=datetime.fromisoformat(m["timestamp"]) if m.get("timestamp") else None,
                )
                for m in messages
            ]

    async def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """获取最近 n 条消息"""
        all_items = await self.get_all()
        return all_items[-n:] if n > 0 else []

    async def clear(self) -> None:
        """清空对话（删除数据库记录）"""
        async with await self._get_session() as session:
            await session.execute(
                delete(Conversation).where(
                    Conversation.conversation_id == self.conversation_id
                )
            )
            await session.commit()

        logger.info(f"[DBStorage] 对话已清空 | conversation={self.conversation_id}")
