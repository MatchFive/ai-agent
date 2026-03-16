"""
Agent基类定义
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable, AsyncGenerator
from pydantic import BaseModel, Field
from enum import Enum

from core.llm import LLMClient, LLMResponse
from core.memory import Memory
from core.logger import logger


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None


class Tool(BaseModel):
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    handler: Optional[Callable] = None  # 工具处理函数

    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """
    Agent基类
    所有具体Agent都应继承此类
    """

    def __init__(
        self,
        name: str,
        description: str,
        llm_client: Optional[LLMClient] = None,
        memory: Optional[Memory] = None,
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        self.name = name
        self.description = description
        self.llm = llm_client or LLMClient()
        self.memory = memory or Memory(system_prompt=system_prompt)
        self.tools: Dict[str, Tool] = {}
        self.status = AgentStatus.IDLE
        self.config = kwargs

        # 注册工具
        if tools:
            for tool in tools:
                self.register_tool(tool)

        logger.info(f"Agent '{name}' initialized with {len(self.tools)} tools")

    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool
        logger.debug(f"Tool '{tool.name}' registered to agent '{self.name}'")

    def unregister_tool(self, tool_name: str) -> bool:
        """注销工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.debug(f"Tool '{tool_name}' unregistered from agent '{self.name}'")
            return True
        return False

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found"
            )

        if not tool.handler:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool '{tool_name}' has no handler"
            )

        try:
            logger.info(f"Executing tool '{tool_name}' with args: {kwargs}")
            result = await tool.handler(**kwargs) if callable(tool.handler) else tool.handler
            return ToolResult(success=True, result=result)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolResult(success=False, result=None, error=str(e))

    @abstractmethod
    async def run(self, input_text: str, **kwargs) -> str:
        """
        运行Agent的主方法

        Args:
            input_text: 用户输入
            **kwargs: 额外参数

        Returns:
            Agent响应
        """
        pass

    async def chat(self, message: str, stream: bool = False, **kwargs) -> Any:
        """
        与Agent对话

        Args:
            message: 用户消息
            stream: 是否使用流式输出
            **kwargs: 额外参数

        Returns:
            响应或响应生成器
        """
        # 添加用户消息到记忆
        await self.memory.add_user_message(message)

        self.status = AgentStatus.RUNNING

        try:
            if stream:
                return self._stream_response(message, **kwargs)
            else:
                response = await self.run(message, **kwargs)
                await self.memory.add_assistant_message(response)
                self.status = AgentStatus.IDLE
                return response
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"Agent '{self.name}' error: {e}")
            raise

    async def _stream_response(
        self,
        message: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式响应"""
        full_response = ""
        async for chunk in self.run_stream(message, **kwargs):
            full_response += chunk
            yield chunk

        await self.memory.add_assistant_message(full_response)
        self.status = AgentStatus.IDLE

    async def run_stream(self, input_text: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式运行Agent（可选实现）
        """
        # 默认实现：非流式
        response = await self.run(input_text, **kwargs)
        yield response

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "tools_count": len(self.tools),
        }

    async def reset(self) -> None:
        """重置Agent状态"""
        await self.memory.clear()
        self.status = AgentStatus.IDLE
        logger.info(f"Agent '{self.name}' reset")
