"""
认证路由
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import jwt

from core.config import settings
from api.models.user import User, InviteCode, get_session
from api.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(user: User) -> str:
    """创建访问令牌"""
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": user.id,
        "exp": expire,
        "role": user.role
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


@router.post("/register", response_model=Token, summary="用户注册")
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    用户注册
    - 需要有效的邀请码
    - 邀请码仅能使用一次
    """
    # 检查用户名是否已存在
    result = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 验证邀请码
    result = await session.execute(
        select(InviteCode).where(InviteCode.code == user_data.invite_code)
    )
    invite_code = result.scalar_one_or_none()

    if not invite_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码不存在"
        )

    if invite_code.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码已被使用"
        )

    # 创建用户
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role="user",
        is_active=True
    )
    session.add(user)
    await session.flush()  # 获取user.id

    # 标记邀请码为已使用
    invite_code.is_used = True
    invite_code.used_by = user.id
    invite_code.used_at = datetime.utcnow()

    await session.commit()
    await session.refresh(user)

    # 生成token
    access_token = create_access_token(user)

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    """
    用户登录
    - 支持管理员和普通用户
    """
    # 查询用户
    result = await session.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    # 生成token
    access_token = create_access_token(user)

    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse.model_validate(current_user)
