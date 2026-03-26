"""
LLM接口封装模块
使用 openai 库对接国内大模型（OpenAI 兼容接口）
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


class OpenAIClient(BaseLLMClient):
    """OpenAI 兼容接口客户端（支持国内大模型）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or settings.llm_api_key
        self.model = model or settings.llm_model
        self.base_url = base_url or settings.llm_base_url
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self._client = None

    def _get_client(self):
        """延迟初始化客户端"""
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
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

        # 构建消息列表，system 消息放在最前面
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(m.to_dict() for m in messages if m.role != "system")

        response = await client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            },
            finish_reason=choice.finish_reason or "",
        )

    async def chat_stream(
        self,
        messages: List[Message],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        client = self._get_client()

        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend(m.to_dict() for m in messages if m.role != "system")

        stream = await client.chat.completions.create(
            model=self.model,
            messages=chat_messages,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


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
        self.provider = provider or settings.llm_provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def _get_client(self) -> BaseLLMClient:
        """获取对应provider的客户端"""
        cache_key = f"{self.provider}_{self.model}"

        if cache_key not in self._clients:
            if self.provider == "openai":
                self._clients[cache_key] = OpenAIClient(
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
