"""
LLM接口封装模块
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncGenerator, Union

from pydantic import BaseModel

from .config import settings
from .logger import logger


class Message(BaseModel):
    """消息模型"""
    role: str  # system, user, assistant
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMResponse(BaseModel):
    """LLM响应模型"""
    content: str
    model: str
    usage: Dict[str, int] = {}
    finish_reason: str = ""


class BaseLLMClient(ABC):
    """LLM客户端基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        pass


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or settings.llm.api_key
        self.model = model or settings.llm.model
        self.base_url = base_url or settings.llm.base_url
        self.max_tokens = settings.llm.max_tokens
        self.temperature = settings.llm.temperature
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def chat(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""
        client = self._get_client()

        # 分离system消息
        system_prompt = system
        chat_messages = [m.to_dict() for m in messages if m.role != "system"]

        extra_args = {
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if system_prompt:
            extra_args["system"] = system_prompt

        response = await client.messages.create(
            model=self.model,
            messages=chat_messages,
            **extra_args
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    async def chat_stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        client = self._get_client()

        chat_messages = [m.to_dict() for m in messages if m.role != "system"]

        extra_args = {
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
        }
        if system:
            extra_args["system"] = system

        async with client.messages.stream(
            model=self.model,
            messages=chat_messages,
            **extra_args
        ) as stream:
            async for text in stream.text_stream:
                yield text


class LLMClient:
    """统一的LLM客户端接口"""

    _clients: Dict[str, BaseLLMClient] = {}

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider or settings.llm.provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def _get_client(self) -> BaseLLMClient:
        """获取对应provider的客户端"""
        cache_key = f"{self.provider}_{self.model}"

        if cache_key not in self._clients:
            if self.provider == "anthropic":
                self._clients[cache_key] = AnthropicClient(
                    api_key=self.api_key,
                    model=self.model,
                    base_url=self.base_url,
                )
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        return self._clients[cache_key]

    async def chat(
        self,
        messages: Union[List[Message], List[Dict]],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """发送对话请求"""
        # 转换消息格式
        formatted_messages = []
        for m in messages:
            if isinstance(m, dict):
                formatted_messages.append(Message(**m))
            else:
                formatted_messages.append(m)

        client = self._get_client()
        return await client.chat(formatted_messages, system=system, **kwargs)

    async def chat_stream(
        self,
        messages: Union[List[Message], List[Dict]],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        formatted_messages = []
        for m in messages:
            if isinstance(m, dict):
                formatted_messages.append(Message(**m))
            else:
                formatted_messages.append(m)

        client = self._get_client()
        async for chunk in client.chat_stream(formatted_messages, system=system, **kwargs):
            yield chunk
