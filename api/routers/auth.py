"""
认证路由
"""

import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import jwt

from core.config import settings
from core.logger import logger
from api.models.user import User, InviteCode, get_session
from api.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    ChangePasswordRequest,
    SendVerifyCodeRequest,
    BindEmailRequest,
)
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 内存存储验证码（生产环境可用 Redis）
_verify_codes = {}  # {email: {"code": "123456", "expires_at": datetime, "purpose": "bind_email"}}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(user: User) -> str:
    """创建访问令牌"""
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": user.uid,  # 使用 uid 作为唯一标识
        "exp": expire,
        "role": user.role
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _generate_code(length: int = 6) -> str:
    """生成数字验证码"""
    return ''.join(random.choices(string.digits, k=length))


async def _send_verify_email(email: str, code: str, purpose: str = "bind_email"):
    """发送验证码邮件"""
    from tools.email_tool import EmailTool, EmailContent

    subject_map = {
        "bind_email": "【AI Agent】邮箱绑定验证码",
    }
    body_template = {
        "bind_email": f"""
        <div style="max-width:480px;margin:0 auto;font-family:sans-serif;">
          <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px;border-radius:16px 16px 0 0;text-align:center;">
            <h2 style="color:#fff;margin:0;font-size:22px;">AI Agent</h2>
            <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">邮箱绑定验证</p>
          </div>
          <div style="background:#fff;padding:32px;border-radius:0 0 16px 16px;border:1px solid #e5e7eb;">
            <p style="color:#374151;font-size:15px;margin:0 0 20px;">您正在进行邮箱绑定操作，验证码为：</p>
            <div style="background:#f3f4f6;border-radius:12px;padding:16px;text-align:center;margin:0 0 20px;">
              <span style="font-size:32px;font-weight:700;color:#6366f1;letter-spacing:8px;">{code}</span>
            </div>
            <p style="color:#6b7280;font-size:13px;margin:0;">验证码 10 分钟内有效，请勿泄露给他人。</p>
          </div>
        </div>
        """
    }

    email_tool = EmailTool()
    content = EmailContent(
        to=email,
        subject=subject_map.get(purpose, "验证码"),
        body=body_template.get(purpose, f"验证码：{code}"),
        html=True,
    )
    result = await email_tool.send_async(content)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"邮件发送失败：{result.get('error', '未知错误')}"
        )


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


@router.put("/password", summary="修改密码")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    修改当前用户密码
    - 需要验证旧密码
    - 新密码至少6位
    """
    if not verify_password(body.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    current_user.password_hash = get_password_hash(body.new_password)
    await session.commit()

    return {"message": "密码修改成功", "success": True}


# ==================== 邮箱绑定 ====================

@router.post("/email/send-code", summary="发送邮箱验证码")
async def send_email_verify_code(
    body: SendVerifyCodeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    发送邮箱绑定验证码
    - 每个邮箱60秒内只能发送一次
    """
    email = body.email.strip()

    # 检查邮箱是否已被其他用户绑定
    result = await session.execute(
        select(User).where(User.email == email, User.id != current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被其他账号绑定"
        )

    # 如果自己已经绑定了这个邮箱
    if current_user.email == email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已绑定当前账号"
        )

    # 防止频繁发送
    existing = _verify_codes.get(email)
    if existing and existing["expires_at"] > datetime.utcnow() + timedelta(minutes=9):
        remaining = (existing["expires_at"] - datetime.utcnow()).seconds
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请 {remaining} 秒后再试"
        )

    # 生成验证码
    code = _generate_code()
    _verify_codes[email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "purpose": "bind_email",
        "user_id": current_user.id,
    }

    # 发送邮件
    await _send_verify_email(email, code)

    logger.info(f"发送邮箱验证码 | user={current_user.username} | email={email}")

    return {"message": "验证码已发送", "success": True}


@router.post("/email/bind", summary="绑定邮箱")
async def bind_email(
    body: BindEmailRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    绑定邮箱
    - 需要正确的验证码
    """
    email = body.email.strip()
    code = body.code

    # 检查邮箱是否已被其他用户绑定
    result = await session.execute(
        select(User).where(User.email == email, User.id != current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被其他账号绑定"
        )

    # 验证码校验
    record = _verify_codes.get(email)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先发送验证码"
        )

    if record["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码不匹配"
        )

    if record["expires_at"] < datetime.utcnow():
        # 清理过期
        del _verify_codes[email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码已过期，请重新发送"
        )

    if record["code"] != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )

    # 绑定邮箱
    current_user.email = email
    await session.commit()

    # 清理已用验证码
    del _verify_codes[email]

    logger.info(f"绑定邮箱成功 | user={current_user.username} | email={email}")

    return {"message": "邮箱绑定成功", "success": True, "email": email}


@router.delete("/email", summary="解绑邮箱")
async def unbind_email(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """解绑当前邮箱"""
    if not current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前未绑定邮箱"
        )

    current_user.email = None
    await session.commit()

    return {"message": "邮箱已解绑", "success": True}
