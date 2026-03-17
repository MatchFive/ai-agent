"""
管理员路由
"""

import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.models.user import User, InviteCode, get_session
from api.schemas.user import (
    UserResponse,
    InviteCodeCreate,
    InviteCodeResponse,
    InviteCodeListResponse,
)
from api.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["管理员"])


def generate_invite_code() -> str:
    """生成邀请码"""
    return secrets.token_urlsafe(16)[:20]


@router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取用户列表（仅管理员）"""
    # 统计总数
    count_result = await session.execute(select(func.count(User.id)))
    total = count_result.scalar()

    # 分页查询
    offset = (page - 1) * page_size
    result = await session.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    users = result.scalars().all()

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/users/{user_id}/toggle-active", summary="启用/禁用用户")
async def toggle_user_active(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """启用或禁用用户"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用管理员账号"
        )

    user.is_active = not user.is_active
    await session.commit()

    return {
        "message": f"用户已{'启用' if user.is_active else '禁用'}",
        "is_active": user.is_active
    }


@router.post("/invite-codes", response_model=list[InviteCodeResponse], summary="生成邀请码")
async def create_invite_codes(
    data: InviteCodeCreate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """
    生成邀请码（仅管理员）
    - 可一次生成多个
    """
    codes = []
    for _ in range(data.count):
        code = InviteCode(
            code=generate_invite_code(),
            created_by=current_admin.id,
            is_used=False
        )
        session.add(code)
        codes.append(code)

    await session.commit()

    for code in codes:
        await session.refresh(code)

    return [InviteCodeResponse.model_validate(c) for c in codes]


@router.get("/invite-codes", response_model=InviteCodeListResponse, summary="获取邀请码列表")
async def list_invite_codes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_used: bool = Query(None, description="筛选状态：true=已使用，false=未使用"),
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取邀请码列表（仅管理员）"""
    query = select(InviteCode)

    if is_used is not None:
        query = query.where(InviteCode.is_used == is_used)

    # 统计总数
    count_query = select(func.count(InviteCode.id))
    if is_used is not None:
        count_query = count_query.where(InviteCode.is_used == is_used)
    count_result = await session.execute(count_query)
    total = count_result.scalar()

    # 分页查询
    offset = (page - 1) * page_size
    query = query.order_by(InviteCode.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(query)
    codes = result.scalars().all()

    return InviteCodeListResponse(
        items=[InviteCodeResponse.model_validate(c) for c in codes],
        total=total
    )


@router.delete("/invite-codes/{code_id}", summary="删除邀请码")
async def delete_invite_code(
    code_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """删除邀请码（仅管理员）"""
    result = await session.execute(
        select(InviteCode).where(InviteCode.id == code_id)
    )
    code = result.scalar_one_or_none()

    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀请码不存在"
        )

    if code.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除已使用的邀请码"
        )

    await session.delete(code)
    await session.commit()

    return {"message": "邀请码已删除"}


@router.get("/stats", summary="获取统计数据")
async def get_stats(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取统计数据（仅管理员）"""
    # 用户总数
    user_count = (await session.execute(
        select(func.count(User.id)).where(User.role == "user")
    )).scalar()

    # 活跃用户
    active_user_count = (await session.execute(
        select(func.count(User.id)).where(User.role == "user", User.is_active == True)
    )).scalar()

    # 邀请码统计
    total_codes = (await session.execute(
        select(func.count(InviteCode.id))
    )).scalar()

    used_codes = (await session.execute(
        select(func.count(InviteCode.id)).where(InviteCode.is_used == True)
    )).scalar()

    unused_codes = total_codes - used_codes

    return {
        "users": {
            "total": user_count,
            "active": active_user_count,
            "inactive": user_count - active_user_count
        },
        "invite_codes": {
            "total": total_codes,
            "used": used_codes,
            "unused": unused_codes
        }
    }
