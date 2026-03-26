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


class GoldPriceData(BaseModel):
    """黄金价格数据"""
    price: float = Field(..., description="价格")
    currency: str = Field(default="USD", description="货币")
    change: Optional[float] = Field(default=None, description="涨跌额")
    change_percent: Optional[float] = Field(default=None, description="涨跌幅")
    timestamp: str = Field(..., description="时间戳")
    source: str = Field(..., description="数据来源")


class StockData(BaseModel):
    """股票数据"""
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(default=None, description="公司名称")
    price: float = Field(..., description="当前价格")
    change: Optional[float] = Field(default=None, description="涨跌额")
    change_percent: Optional[float] = Field(default=None, description="涨跌幅")
    volume: Optional[int] = Field(default=None, description="成交量")
    timestamp: str = Field(..., description="时间戳")
    source: str = Field(..., description="数据来源")


class NewsItem(BaseModel):
    """新闻条目"""
    title: str = Field(..., description="标题")
    source: str = Field(..., description="来源")
    url: str = Field(..., description="链接")
    published_at: str = Field(..., description="发布时间")
    summary: Optional[str] = Field(default=None, description="摘要")


class NewsResponse(BaseModel):
    """新闻响应"""
    articles: List[NewsItem] = Field(..., description="新闻列表")
    total: int = Field(..., description="总数")
    source: str = Field(..., description="数据来源")


class AgentInfo(BaseModel):
    """Agent 信息"""
    name: str = Field(..., description="Agent名称")
    description: str = Field(..., description="Agent描述")
    tools: List[str] = Field(..., description="可用工具列表")
