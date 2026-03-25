"""
用户相关 schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ========== 用户相关 ==========

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")


class UserCreate(UserBase):
    """用户注册模型"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    invite_code: str = Field(..., min_length=1, description="邀请码")


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    uid: str
    role: str
    is_active: bool
    created_at: datetime


# ========== Token相关 ==========

class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Token载荷"""
    sub: str  # user uid
    exp: datetime
    role: str


# ========== 邀请码相关 ==========

class InviteCodeCreate(BaseModel):
    """创建邀请码"""
    count: int = Field(default=1, ge=1, le=100, description="生成数量")


class InviteCodeResponse(BaseModel):
    """邀请码响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    is_used: bool
    created_by: int
    used_by: Optional[int] = None
    created_at: datetime
    used_at: Optional[datetime] = None


class InviteCodeListResponse(BaseModel):
    """邀请码列表响应"""
    items: List[InviteCodeResponse]
    total: int
