"""
Agent 对话路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

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
)
from api.models.conversation import DatabaseStorage, Conversation
from agents.manager import agent_manager
from agents.base import BaseAgent
from core.logger import logger

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

        # 调用 Agent
        response = await agent.run(request.message)

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

    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 流式响应
            async for chunk in agent.run_stream(request.message):
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
