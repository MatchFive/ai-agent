"""
管理员 - 工具和Agent配置路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.models.user import User, get_session
from api.models.agent_config import AgentConfig, ToolConfig, AgentToolConfig, KnowledgeBase
from api.schemas.admin_tools import (
    ToolConfigResponse,
    ToolConfigUpdate,
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    ToolAssignmentRequest,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)
from api.deps import get_current_admin
from core.logger import logger

router = APIRouter(prefix="/admin", tags=["管理员-工具与Agent"])


# ==================== 工具管理 ====================

@router.get("/tools", summary="获取工具列表")
async def list_tools(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取所有已注册的工具"""
    from tools.registry import ToolRegistry

    result = await session.execute(
        select(ToolConfig).order_by(ToolConfig.category, ToolConfig.name)
    )
    db_tools = result.scalars().all()

    tools = []
    for t in db_tools:
        reg = ToolRegistry.get(t.name)
        synced = reg.version_hash == t.version_hash if reg else False
        resp = ToolConfigResponse.model_validate(t)
        resp.synced = synced
        tools.append(resp)

    return {"items": tools, "total": len(tools)}


@router.post("/tools/reload", summary="重新扫描并同步工具")
async def reload_tools(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """重新扫描装饰器并同步到数据库"""
    from core.startup import import_tools, sync_tools_to_db, load_agents_from_db

    import_tools()
    await sync_tools_to_db()
    await load_agents_from_db()

    from tools.registry import ToolRegistry
    return {
        "message": "工具重新扫描完成",
        "tools_count": len(ToolRegistry.get_all())
    }


@router.get("/tools/{tool_id}", summary="获取工具详情")
async def get_tool(
    tool_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取工具详情"""
    result = await session.execute(
        select(ToolConfig).where(ToolConfig.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工具不存在")

    from tools.registry import ToolRegistry
    reg = ToolRegistry.get(tool.name)
    resp = ToolConfigResponse.model_validate(tool)
    resp.synced = reg.version_hash == tool.version_hash if reg else False
    return resp


@router.put("/tools/{tool_id}", summary="更新工具配置")
async def update_tool(
    tool_id: int,
    data: ToolConfigUpdate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """更新工具元信息"""
    result = await session.execute(
        select(ToolConfig).where(ToolConfig.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工具不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)

    await session.commit()
    await session.refresh(tool)
    return ToolConfigResponse.model_validate(tool)


@router.patch("/tools/{tool_id}", summary="启用/禁用工具")
async def toggle_tool(
    tool_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """启用或禁用工具"""
    result = await session.execute(
        select(ToolConfig).where(ToolConfig.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工具不存在")

    tool.is_active = not tool.is_active
    await session.commit()
    await session.refresh(tool)

    return {
        "message": f"工具已{'启用' if tool.is_active else '禁用'}",
        "is_active": tool.is_active
    }


# ==================== Agent 管理 ====================

@router.get("/agents", summary="获取Agent列表")
async def list_agents(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取所有Agent配置"""
    result = await session.execute(
        select(AgentConfig).order_by(AgentConfig.created_at.desc())
    )
    agents = result.scalars().all()

    items = []
    for agent in agents:
        # 获取关联的工具
        tool_result = await session.execute(
            select(ToolConfig, AgentToolConfig.sort_order)
            .join(AgentToolConfig, AgentToolConfig.tool_id == ToolConfig.id)
            .where(AgentToolConfig.agent_id == agent.id, ToolConfig.is_active == True)
            .order_by(AgentToolConfig.sort_order)
        )
        tool_rows = tool_result.all()

        from tools.registry import ToolRegistry
        tools = []
        for t, sort_order in tool_rows:
            reg = ToolRegistry.get(t.name)
            resp = ToolConfigResponse.model_validate(t)
            resp.synced = reg.version_hash == t.version_hash if reg else False
            tools.append(resp)

        resp = AgentConfigResponse.model_validate(agent)
        resp.tools = tools
        items.append(resp)

    return {"items": items, "total": len(items)}


@router.post("/agents", summary="创建Agent")
async def create_agent(
    data: AgentConfigCreate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """创建Agent配置"""
    # 检查名称唯一
    existing = await session.execute(
        select(AgentConfig).where(AgentConfig.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent名称已存在")

    agent = AgentConfig(
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        agent_class=data.agent_class,
        config_json=data.config_json,
    )
    session.add(agent)
    await session.flush()

    # 关联工具
    for idx, tool_id in enumerate(data.tool_ids):
        tool = await session.execute(
            select(ToolConfig).where(ToolConfig.id == tool_id)
        )
        if tool.scalar_one_or_none():
            session.add(AgentToolConfig(
                agent_id=agent.id,
                tool_id=tool_id,
                sort_order=idx
            ))

    await session.commit()
    await session.refresh(agent)

    logger.info(f"Agent '{data.name}' created by admin {current_admin.username}")
    return AgentConfigResponse.model_validate(agent)


@router.get("/agents/{agent_id}", summary="获取Agent详情")
async def get_agent(
    agent_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取Agent详情（含关联工具）"""
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent不存在")

    tool_result = await session.execute(
        select(ToolConfig, AgentToolConfig.sort_order)
        .join(AgentToolConfig, AgentToolConfig.tool_id == ToolConfig.id)
        .where(AgentToolConfig.agent_id == agent.id, ToolConfig.is_active == True)
        .order_by(AgentToolConfig.sort_order)
    )
    tool_rows = tool_result.all()

    from tools.registry import ToolRegistry
    tools = []
    for t, sort_order in tool_rows:
        reg = ToolRegistry.get(t.name)
        resp = ToolConfigResponse.model_validate(t)
        resp.synced = reg.version_hash == t.version_hash if reg else False
        tools.append(resp)

    resp = AgentConfigResponse.model_validate(agent)
    resp.tools = tools
    return resp


@router.put("/agents/{agent_id}", summary="更新Agent配置")
async def update_agent(
    agent_id: int,
    data: AgentConfigUpdate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """更新Agent配置"""
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await session.commit()
    await session.refresh(agent)

    logger.info(f"Agent '{agent.name}' updated by admin {current_admin.username}")
    return AgentConfigResponse.model_validate(agent)


@router.patch("/agents/{agent_id}", summary="启用/禁用Agent")
async def toggle_agent(
    agent_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """启用或禁用Agent"""
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent不存在")

    agent.is_active = not agent.is_active
    await session.commit()
    await session.refresh(agent)

    # 同步到内存中的 agent_manager
    from agents.manager import agent_manager
    if agent.is_active:
        from core.startup import load_agents_from_db
        await load_agents_from_db()
    else:
        mem_agent = agent_manager.get(agent.name)
        if mem_agent:
            agent_manager.unregister(agent.name)

    return {
        "message": f"Agent已{'启用' if agent.is_active else '禁用'}",
        "is_active": agent.is_active
    }


@router.delete("/agents/{agent_id}", summary="删除Agent")
async def delete_agent(
    agent_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """删除Agent配置"""
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent不存在")

    agent_name = agent.name
    await session.delete(agent)
    await session.commit()

    # 从内存中移除
    from agents.manager import agent_manager
    agent_manager.unregister(agent_name)

    logger.info(f"Agent '{agent_name}' deleted by admin {current_admin.username}")
    return {"message": "Agent已删除"}


# ==================== Agent-Tool 关联管理 ====================

@router.post("/agents/{agent_id}/tools", summary="设置Agent的工具关联")
async def set_agent_tools(
    agent_id: int,
    data: ToolAssignmentRequest,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """批量设置Agent关联的工具（替换现有关联）"""
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent不存在")

    # 删除旧关联
    await session.execute(
        AgentToolConfig.__table__.delete().where(
            AgentToolConfig.agent_id == agent_id
        )
    )

    # 添加新关联
    for idx, tool_id in enumerate(data.tool_ids):
        tool = await session.execute(
            select(ToolConfig).where(ToolConfig.id == tool_id)
        )
        if tool.scalar_one_or_none():
            session.add(AgentToolConfig(
                agent_id=agent_id,
                tool_id=tool_id,
                sort_order=idx
            ))

    await session.commit()

    logger.info(
        f"Agent '{agent.name}' tools updated: {data.tool_ids} "
        f"by admin {current_admin.username}"
    )
    return {"message": "工具关联已更新", "tool_count": len(data.tool_ids)}


@router.delete("/agents/{agent_id}/tools/{tool_id}", summary="移除Agent的工具关联")
async def remove_agent_tool(
    agent_id: int,
    tool_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """移除Agent的某个工具关联"""
    result = await session.execute(
        select(AgentToolConfig).where(
            AgentToolConfig.agent_id == agent_id,
            AgentToolConfig.tool_id == tool_id
        )
    )
    relation = result.scalar_one_or_none()
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关联不存在")

    await session.delete(relation)
    await session.commit()

    return {"message": "工具关联已移除"}


# ==================== 知识库管理 ====================

@router.get("/knowledge-bases", summary="获取知识库列表")
async def list_knowledge_bases(
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取所有知识库"""
    result = await session.execute(
        select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
    )
    items = result.scalars().all()
    return {"items": items, "total": len(items)}


@router.post("/knowledge-bases", summary="创建知识库")
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """创建知识库"""
    existing = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="知识库名称已存在")

    kb = KnowledgeBase(
        name=data.name,
        description=data.description,
        collection_name=data.collection_name,
        embedding_dim=data.embedding_dim,
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)

    logger.info(f"知识库 '{data.name}' created by admin {current_admin.username}")
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/knowledge-bases/{kb_id}", summary="获取知识库详情")
async def get_knowledge_base(
    kb_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """获取知识库详情"""
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")
    return KnowledgeBaseResponse.model_validate(kb)


@router.put("/knowledge-bases/{kb_id}", summary="更新知识库")
async def update_knowledge_base(
    kb_id: int,
    data: KnowledgeBaseUpdate,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """更新知识库配置"""
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kb, field, value)

    await session.commit()
    await session.refresh(kb)

    logger.info(f"知识库 '{kb.name}' updated by admin {current_admin.username}")
    return KnowledgeBaseResponse.model_validate(kb)


@router.patch("/knowledge-bases/{kb_id}", summary="启用/禁用知识库")
async def toggle_knowledge_base(
    kb_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """启用或禁用知识库"""
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    kb.is_active = not kb.is_active
    await session.commit()
    await session.refresh(kb)

    return {
        "message": f"知识库已{'启用' if kb.is_active else '禁用'}",
        "is_active": kb.is_active
    }


@router.delete("/knowledge-bases/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int,
    current_admin: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session)
):
    """删除知识库"""
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库不存在")

    kb_name = kb.name
    await session.delete(kb)
    await session.commit()

    logger.info(f"知识库 '{kb_name}' deleted by admin {current_admin.username}")
    return {"message": "知识库已删除"}
