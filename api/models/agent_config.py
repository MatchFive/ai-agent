"""
Agent 和 Tool 配置数据库模型
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from api.models.user import Base


class AgentConfig(Base):
    """Agent配置表"""
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="Agent标识名")
    description = Column(String(500), nullable=False, default="", comment="Agent描述")
    system_prompt = Column(Text, nullable=False, default="", comment="系统提示词")
    agent_class = Column(String(200), nullable=False, default="", comment="Python类路径")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    config_json = Column(Text, nullable=False, default="{}", comment="扩展配置JSON")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    tool_relations = relationship(
        "AgentToolConfig",
        back_populates="agent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class ToolConfig(Base):
    """工具配置表"""
    __tablename__ = "tool_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="工具标识名")
    description = Column(String(500), nullable=False, default="", comment="工具描述")
    parameters_json = Column(Text, nullable=False, default="{}", comment="参数JSON Schema")
    handler_class = Column(String(200), nullable=False, default="", comment="handler类路径")
    handler_method = Column(String(100), nullable=False, default="", comment="handler方法名")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    category = Column(String(50), nullable=False, default="general", comment="工具分类")
    version_hash = Column(String(64), nullable=False, default="", comment="版本哈希（用于同步检测）")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    agent_relations = relationship(
        "AgentToolConfig",
        back_populates="tool",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class AgentToolConfig(Base):
    """Agent-工具关联表"""
    __tablename__ = "agent_tool_configs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tool_configs.id", ondelete="CASCADE"), nullable=False)
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    agent = relationship("AgentConfig", back_populates="tool_relations")
    tool = relationship("ToolConfig", back_populates="agent_relations")

    __table_args__ = (
        UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool"),
    )
