"""
Agent 相关 schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    stream: bool = Field(default=False, description="是否流式响应")
    conversation_id: Optional[str] = Field(default=None, description="会话ID")


class AgentChatResponse(BaseModel):
    """Agent 对话响应"""
    conversation_id: str = Field(..., description="会话ID")
    message: ChatMessage = Field(..., description="回复消息")
    tools_used: List[str] = Field(default_factory=list, description="使用的工具列表")


class AgentInfo(BaseModel):
    """Agent 信息"""
    name: str = Field(..., description="Agent名称")
    description: str = Field(..., description="Agent描述")
    tools: List[str] = Field(..., description="可用工具列表")


class ConversationListItem(BaseModel):
    """对话历史列表项"""
    conversation_id: str
    title: str = "新对话"
    agent_name: Optional[str] = None
    message_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConversationDetail(BaseModel):
    """对话详情（含完整消息）"""
    conversation_id: str
    title: str = "新对话"
    agent_name: Optional[str] = None
    messages: List[ChatMessage] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    items: List[ConversationListItem]
    total: int


class UpdateTitleRequest(BaseModel):
    """更新对话标题"""
    title: str = Field(..., min_length=1, max_length=255, description="对话标题")
