"""
Admin 管理工具和 Agent 的 Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ==================== ToolConfig Schemas ====================

class ToolConfigResponse(BaseModel):
    """工具配置响应"""
    id: int
    name: str
    description: str
    parameters_json: str
    handler_class: str
    handler_method: str
    is_active: bool
    category: str
    version_hash: str
    synced: bool = False  # DB版本是否与registry一致
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolConfigUpdate(BaseModel):
    """更新工具配置"""
    description: Optional[str] = None
    parameters_json: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None


# ==================== AgentConfig Schemas ====================

class AgentConfigCreate(BaseModel):
    """创建Agent"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent标识名")
    description: str = Field(..., max_length=500, description="Agent描述")
    system_prompt: str = Field(..., min_length=1, description="系统提示词")
    agent_class: str = Field(default="", description="Python类路径")
    config_json: str = Field(default="{}", description="扩展配置JSON")
    tool_ids: List[int] = Field(default_factory=list, description="关联的工具ID列表")


class AgentConfigUpdate(BaseModel):
    """更新Agent配置"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    agent_class: Optional[str] = None
    config_json: Optional[str] = None
    is_active: Optional[bool] = None


class AgentConfigResponse(BaseModel):
    """Agent配置响应"""
    id: int
    name: str
    description: str
    system_prompt: str
    agent_class: str
    is_active: bool
    config_json: str
    tools: List[ToolConfigResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ToolAssignmentRequest(BaseModel):
    """工具关联请求"""
    tool_ids: List[int] = Field(..., description="工具ID列表")


# ==================== KnowledgeBase Schemas ====================

class KnowledgeBaseCreate(BaseModel):
    """创建知识库"""
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    description: str = Field(default="", max_length=500, description="知识库描述")
    collection_name: str = Field(..., min_length=1, max_length=200, description="Milvus collection名")
    embedding_dim: int = Field(default=1024, description="向量维度")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    collection_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    embedding_dim: Optional[int] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: str
    collection_name: str
    embedding_dim: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
