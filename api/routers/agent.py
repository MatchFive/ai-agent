"""
Agent 对话路由
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import uuid
import json

from api.models.user import User
from api.deps import get_current_user
from api.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    ChatMessage,
    AgentInfo
)
from api.models.conversation import DatabaseStorage
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


def _setup_conversation(agent: BaseAgent, conversation_id: str, user_id: int = None):
    """设置 Agent 使用数据库存储的指定会话"""
    storage = DatabaseStorage(conversation_id, user_id=user_id)
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
        _setup_conversation(agent, conversation_id, user_id=current_user.id)

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
    _setup_conversation(agent, conversation_id, user_id=current_user.id)

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
