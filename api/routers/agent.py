"""
Agent 对话路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
import asyncio
from typing import Optional

from api.models.user import User, get_session
from api.deps import get_current_user
from api.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    ChatMessage,
    AgentInfo,
    ConversationListItem,
    ConversationDetail,
    ConversationListResponse,
    UpdateTitleRequest,
    MemoryItemSchema,
    MemoryListResponse,
    SaveExperienceRequest,
)
from api.models.conversation import DatabaseStorage, Conversation, UserLongTermMemory, AgentExperience
from agents.manager import agent_manager
from agents.base import BaseAgent
from core.logger import logger
from core.config import settings

router = APIRouter(prefix="/agent", tags=["Agent"])


def get_agent(agent_name: str = "InvestmentAgent") -> BaseAgent:
    """从 agent_manager 获取 Agent 实例"""
    agent = agent_manager.get(agent_name)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 未找到或未启用")
    return agent


def _setup_conversation(agent: BaseAgent, conversation_id: str, user_id: int = None, agent_name: str = None):
    """设置 Agent 使用数据库存储的指定会话"""
    storage = DatabaseStorage(conversation_id, user_id=user_id, agent_name=agent_name)
    agent.memory.set_storage(storage)


def _is_ltm_enabled(agent: BaseAgent) -> bool:
    """检查该 Agent 是否启用了长期记忆"""
    config = getattr(agent, 'config', {})
    if isinstance(config, dict):
        ltm_config = config.get("long_term_memory", {})
        if isinstance(ltm_config, dict):
            return ltm_config.get("enabled", settings.ltm_enabled)
    return settings.ltm_enabled


async def _inject_long_term_memories(agent: BaseAgent, user_id: int, query: str):
    """检索并注入长期记忆到 Agent 的短期记忆中"""
    from core.long_term_memory import long_term_memory_manager
    memories = await long_term_memory_manager.retrieve(user_id, query, agent.name)
    if memories:
        context = long_term_memory_manager.format_memories_as_context(memories)
        await agent.memory.add_system_message(context)


def _is_experience_kb_enabled(agent: BaseAgent) -> bool:
    """检查该 Agent 是否启用了经验知识库检索"""
    config = getattr(agent, 'config', {})
    if isinstance(config, dict):
        exp_config = config.get("experience_kb", {})
        if isinstance(exp_config, dict):
            return exp_config.get("enabled", False)
    return False


async def _inject_experiences(agent: BaseAgent, query: str):
    """检索经验库并注入到 Agent 的短期记忆中"""
    try:
        from core.vectorstore import vectorstore
        from core.embedding import embedding_client

        query_embedding = await embedding_client.embed_single(query)

        results = await vectorstore.search(
            query_embedding=query_embedding,
            collection_name="agent_experiences",
            top_k=3,
            output_fields=["id", "question", "answer", "agent_name"],
        )

        if not results:
            return

        lines = ["[相关经验]"]
        hit_ids = []
        for item in results:
            question = item.get("question", "")
            answer = item.get("answer", "")
            lines.append(f"问题：{question}")
            lines.append(f"回答：{answer}")
            lines.append("")
            hit_ids.append(item.get("id"))

        await agent.memory.add_system_message("\n".join(lines).strip())
        logger.info(f"[经验检索] Agent '{agent.name}' 检索到 {len(results)} 条相关经验")

        # 异步更新命中记录
        if hit_ids:
            asyncio.create_task(_record_experience_hits(hit_ids))

    except Exception as e:
        logger.warning(f"经验检索失败（不影响正常回答）: {e}")


@router.get("/info", response_model=AgentInfo, summary="获取Agent信息")
async def get_agent_info(agent: BaseAgent = Depends(get_agent)):
    """获取当前 Agent 的信息"""
    return AgentInfo(
        name=agent.name,
        description=agent.description,
        tools=list(agent.tools.keys())
    )


@router.get("/list", summary="获取所有可用Agent")
async def list_agents():
    """获取所有已注册的 Agent 列表"""
    agents = agent_manager.list_agents()
    return {"items": agents, "total": len(agents)}


@router.post("/chat", response_model=AgentChatResponse, summary="对话（非流式）")
async def chat(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    agent: BaseAgent = Depends(get_agent)
):
    """
    与 Agent 对话（非流式）

    - message: 用户消息
    - stream: 是否流式响应（此处为 false）
    - conversation_id: 会话ID（可选，用于连续对话）
    """
    try:
        # 生成或使用现有会话 ID
        conversation_id = request.conversation_id or str(uuid.uuid4())

        logger.info(f"User {current_user.username} chatting with {agent.name}, conversation: {conversation_id}")

        # 设置数据库存储
        _setup_conversation(agent, conversation_id, user_id=current_user.id, agent_name=agent.name)

        # 注入长期记忆
        if _is_ltm_enabled(agent):
            await _inject_long_term_memories(agent, current_user.id, request.message)

        # 注入经验知识库
        if _is_experience_kb_enabled(agent):
            await _inject_experiences(agent, request.message)

        # 调用 Agent
        response = await agent.run(request.message)

        # 后台异步提取长期记忆
        if _is_ltm_enabled(agent) and response:
            from core.long_term_memory import long_term_memory_manager
            asyncio.create_task(
                long_term_memory_manager.extract_and_store(
                    user_id=current_user.id,
                    user_message=request.message,
                    assistant_message=response,
                    agent_name=agent.name,
                    conversation_id=conversation_id,
                )
            )

        return AgentChatResponse(
            conversation_id=conversation_id,
            message=ChatMessage(
                role="assistant",
                content=response
            ),
            tools_used=[]
        )
    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/chat/stream", summary="对话（流式）")
async def chat_stream(
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    agent: BaseAgent = Depends(get_agent)
):
    """
    与 Agent 对话（流式 SSE）

    返回 Server-Sent Events 流：
    - data: {"content": "...", "conversation_id": "..."}
    - data: [DONE]
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    logger.info(f"User {current_user.username} streaming chat with {agent.name}, conversation: {conversation_id}")

    # 设置数据库存储
    _setup_conversation(agent, conversation_id, user_id=current_user.id, agent_name=agent.name)

    # 注入长期记忆
    ltm_enabled = _is_ltm_enabled(agent)
    if ltm_enabled:
        await _inject_long_term_memories(agent, current_user.id, request.message)

    # 注入经验知识库
    if _is_experience_kb_enabled(agent):
        await _inject_experiences(agent, request.message)

    async def event_generator():
        """SSE 事件生成器"""
        full_response = ""
        try:
            # 流式响应
            async for chunk in agent.run_stream(request.message):
                full_response += chunk
                # 检查是否为状态事件
                try:
                    event = json.loads(chunk)
                    if isinstance(event, dict) and event.get("type") == "status":
                        status_data = json.dumps({
                            "type": "status",
                            "content": event["content"],
                            "conversation_id": conversation_id
                        }, ensure_ascii=False)
                        yield f"data: {status_data}\n\n"
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass

                # 普通内容
                data = json.dumps({
                    "content": chunk,
                    "conversation_id": conversation_id
                }, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # 发送结束标记
            yield f"data: [DONE]\n\n"

            # 后台异步提取长期记忆
            if ltm_enabled and full_response:
                from core.long_term_memory import long_term_memory_manager
                asyncio.create_task(
                    long_term_memory_manager.extract_and_store(
                        user_id=current_user.id,
                        user_message=request.message,
                        assistant_message=full_response,
                        agent_name=agent.name,
                        conversation_id=conversation_id,
                    )
                )

        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/reset", summary="重置对话")
async def reset_conversation(
    request: AgentChatRequest = None,
    current_user: User = Depends(get_current_user),
    agent: BaseAgent = Depends(get_agent)
):
    """
    重置对话，清空记忆（同时清除数据库记录）
    """
    try:
        # 如果有 conversation_id，先设置 DB 存储再清除
        if request and request.conversation_id:
            _setup_conversation(agent, request.conversation_id, user_id=current_user.id)

        await agent.reset()
        logger.info(f"User {current_user.username} reset conversation with {agent.name}")
        return {"message": "对话已重置", "success": True}
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", summary="获取可用工具列表")
async def list_tools(
    current_user: User = Depends(get_current_user),
    agent: BaseAgent = Depends(get_agent)
):
    """获取 Agent 可用的工具列表"""
    tools = []
    for name, tool in agent.tools.items():
        tools.append({
            "name": name,
            "description": tool.description,
            "parameters": tool.parameters
        })

    return {"tools": tools}


# ==================== 对话历史管理 ====================

@router.get("/conversations", summary="获取对话历史列表")
async def list_conversations(
    agent_name: str = Query(..., description="Agent名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """获取当前用户与指定 Agent 的对话历史列表"""
    query = select(Conversation).where(
        Conversation.user_id == current_user.id,
        Conversation.agent_name == agent_name,
    ).order_by(Conversation.updated_at.desc())

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    conversations = result.scalars().all()

    items = []
    for conv in conversations:
        try:
            messages = json.loads(conv.messages)
            msg_count = len(messages)
        except (json.JSONDecodeError, TypeError):
            msg_count = 0
        items.append(ConversationListItem(
            conversation_id=conv.conversation_id,
            title=conv.title or "新对话",
            agent_name=conv.agent_name,
            message_count=msg_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        ))

    return ConversationListResponse(items=items, total=total)


@router.get("/conversations/{conversation_id}", summary="获取对话详情")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """获取指定对话的完整消息内容"""
    result = await session.execute(
        select(Conversation).where(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    try:
        raw_messages = json.loads(conv.messages)
        messages = [ChatMessage(**m) for m in raw_messages]
    except (json.JSONDecodeError, TypeError):
        messages = []

    return ConversationDetail(
        conversation_id=conv.conversation_id,
        title=conv.title or "新对话",
        agent_name=conv.agent_name,
        messages=messages,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


@router.delete("/conversations/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """删除指定对话"""
    result = await session.execute(
        select(Conversation).where(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    await session.delete(conv)
    await session.commit()
    return {"message": "对话已删除", "success": True}


@router.put("/conversations/{conversation_id}/title", summary="更新对话标题")
async def update_conversation_title(
    conversation_id: str,
    body: UpdateTitleRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """更新对话标题"""
    result = await session.execute(
        select(Conversation).where(
            Conversation.conversation_id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    conv.title = body.title
    await session.commit()
    return {"message": "标题已更新", "success": True}


# ==================== 长期记忆管理 ====================

@router.get("/memories", response_model=MemoryListResponse, summary="获取长期记忆列表")
async def list_memories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=50, description="每页数量"),
    category: Optional[str] = Query(None, description="按类别过滤: preference/fact/context/instruction"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """获取当前用户的长期记忆列表（分页）"""
    query = select(UserLongTermMemory).where(
        UserLongTermMemory.user_id == current_user.id,
    )

    if category:
        query = query.where(UserLongTermMemory.category == category)

    query = query.order_by(UserLongTermMemory.created_at.desc())

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    memories = result.scalars().all()

    items = [
        MemoryItemSchema(
            id=m.id,
            text=m.text,
            category=m.category,
            importance=m.importance,
            agent_name=m.agent_name,
            conversation_id=m.conversation_id,
            created_at=m.created_at,
        )
        for m in memories
    ]

    return MemoryListResponse(items=items, total=total)


@router.delete("/memories/{memory_id}", summary="删除单条长期记忆")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """删除指定的长期记忆（同时删除 Milvus 和 MySQL 记录）"""
    result = await session.execute(
        select(UserLongTermMemory).where(
            UserLongTermMemory.id == memory_id,
            UserLongTermMemory.user_id == current_user.id,
        )
    )
    mem = result.scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=404, detail="记忆不存在")

    # 从 Milvus 删除
    try:
        from core.long_term_memory import long_term_memory_manager
        await long_term_memory_manager.delete_memory(mem.milvus_id)
    except Exception as e:
        logger.warning(f"从 Milvus 删除记忆失败（继续删除 DB 记录）: {e}")

    # 从 MySQL 删除
    await session.delete(mem)
    await session.commit()
    return {"message": "记忆已删除", "success": True}


@router.delete("/memories", summary="清空所有长期记忆")
async def clear_all_memories(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """清空当前用户的所有长期记忆"""
    result = await session.execute(
        select(UserLongTermMemory).where(
            UserLongTermMemory.user_id == current_user.id,
        )
    )
    memories = result.scalars().all()

    if not memories:
        return {"message": "没有需要清除的记忆", "success": True}

    # 从 Milvus 批量删除
    try:
        from core.long_term_memory import long_term_memory_manager
        milvus_ids = [m.milvus_id for m in memories]
        await long_term_memory_manager.delete_memories(milvus_ids)
    except Exception as e:
        logger.warning(f"从 Milvus 批量删除记忆失败（继续删除 DB 记录）: {e}")

    # 从 MySQL 删除
    for mem in memories:
        await session.delete(mem)
    await session.commit()
    return {"message": f"已清空 {len(memories)} 条记忆", "success": True}


# ==================== 经验知识库管理 ====================

@router.post("/experiences", summary="保存经验")
async def save_experience(
    request: SaveExperienceRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    将对话中的一组 Q&A 保存为经验

    - conversation_id: 对话ID
    - question_index: 第几组 Q&A（-1 表示最后一组，默认 -1）
    """
    import time as _time

    # 加载对话
    result = await session.execute(
        select(Conversation).where(
            Conversation.conversation_id == request.conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    # 解析消息
    try:
        messages = json.loads(conv.messages)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="对话消息解析失败")

    # 提取 Q&A 对
    qa_pairs = []
    current_q = None
    for msg in messages:
        if msg.get("role") == "user":
            current_q = msg.get("content", "")
        elif msg.get("role") == "assistant" and current_q:
            qa_pairs.append({"question": current_q, "answer": msg.get("content", "")})
            current_q = None

    if not qa_pairs:
        raise HTTPException(status_code=400, detail="对话中没有有效的问答对")

    # 获取目标 Q&A
    idx = request.question_index if request.question_index >= 0 else len(qa_pairs) - 1
    if idx >= len(qa_pairs):
        raise HTTPException(status_code=400, detail=f"问答对索引越界，共 {len(qa_pairs)} 组")

    qa = qa_pairs[idx]
    question_text = qa["question"][:2000]
    answer_text = qa["answer"][:5000]

    # Embed question 并写入 Milvus
    try:
        from core.vectorstore import vectorstore
        from core.embedding import embedding_client

        query_embedding = await embedding_client.embed_single(question_text)
        now_ts = int(_time.time())

        milvus_ids = await vectorstore.insert("agent_experiences", [{
            "embedding": query_embedding,
            "question": question_text,
            "answer": answer_text,
            "agent_name": conv.agent_name or "unknown",
            "created_at": now_ts,
        }])
        milvus_id = milvus_ids[0] if milvus_ids else 0
    except Exception as e:
        logger.error(f"经验写入 Milvus 失败: {e}")
        raise HTTPException(status_code=500, detail=f"经验存储失败: {str(e)}")

    # 写入 MySQL
    experience = AgentExperience(
        user_id=current_user.id,
        agent_name=conv.agent_name or "unknown",
        question=question_text,
        answer=answer_text,
        milvus_id=milvus_id,
    )
    session.add(experience)
    await session.commit()

    logger.info(
        f"经验已保存 | user={current_user.username} | "
        f"agent={conv.agent_name} | question='{question_text[:30]}...'"
    )
    return {"message": "经验已保存", "success": True, "id": experience.id}


async def _record_experience_hits(milvus_ids: list):
    """更新命中的经验的 hit_count 和 last_referenced_at"""
    from datetime import datetime
    from api.models.user import get_session_factory

    if not milvus_ids:
        return

    factory = get_session_factory()
    if not factory:
        return

    try:
        async with factory() as session:
            result = await session.execute(
                select(AgentExperience).where(
                    AgentExperience.milvus_id.in_(milvus_ids)
                )
            )
            experiences = result.scalars().all()
            now = datetime.utcnow()
            for exp in experiences:
                exp.hit_count = (exp.hit_count or 0) + 1
                exp.last_referenced_at = now
            if experiences:
                await session.commit()
                logger.debug(f"更新 {len(experiences)} 条经验命中记录")
    except Exception as e:
        logger.warning(f"更新经验命中计数失败: {e}")
