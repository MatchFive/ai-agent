"""
Unity 入门小助手 Agent
基于 RAG 的知识问答 Agent
"""

from typing import AsyncGenerator
import json
import asyncio

from agents.base import BaseAgent, Tool
from core.logger import logger


class UnityAgent(BaseAgent):
    """
    Unity 入门小助手
    基于知识库检索回答 Unity 相关问题
    """

    def __init__(
        self,
        name: str = "UnityAgent",
        description: str = "Unity 入门小助手，基于 Unity 使用手册提供学习指导",
        llm_client=None,
        memory=None,
        knowledge_base: str = "Unity手册",
        **kwargs
    ):
        system_prompt = """你是 Unity 入门小助手，专门帮助初学者学习 Unity 游戏引擎。

**你的知识来源**：
- 你可以访问 Unity 使用手册知识库
- 每次回答前，你会先从知识库中检索相关文档片段

**回答规范**：
1. 始终基于检索到的文档内容回答，不要凭空编造
2. 如果检索结果中没有相关信息，诚实告知用户并建议换个关键词
3. 回答要结构清晰、通俗易懂，适合初学者
4. 涉及代码的部分给出示例代码
5. 适当给出操作步骤指引
6. 回复使用中文

**注意事项**：
- 不要声称自己是官方文档，你是基于文档的 AI 助手
- 如果用户的问题与 Unity 无关，礼貌地告知你只回答 Unity 相关问题
- 保持耐心和友好的语气"""

        self.knowledge_base = knowledge_base
        super().__init__(
            name=name,
            description=description,
            llm_client=llm_client,
            memory=memory,
            system_prompt=system_prompt,
            **kwargs
        )

    def _build_context(self, documents: list) -> str:
        """将检索到的文档构建为上下文字符串"""
        if not documents:
            return ""

        parts = []
        for doc in documents:
            text = doc.get("text", "")
            score = doc.get("score", 0)
            parts.append(f"[相关度: {score:.2f}]\n{text}")

        return "\n\n---\n\n".join(parts)

    async def run(self, input_text: str, **kwargs) -> str:
        """
        运行 Agent（非流式）

        1. 调用 RAG 检索相关文档
        2. 将文档注入上下文
        3. 调用 LLM 生成回答
        """
        # 添加用户消息到记忆
        await self.memory.add_user_message(input_text)

        # 1. RAG 检索
        tool_result = await self.execute_tool("rag_search", knowledge_base=self.knowledge_base, query=input_text, top_k=5)

        if tool_result.success and tool_result.result.get("documents"):
            documents = tool_result.result["documents"]
            context = self._build_context(documents)

            # 构建增强的用户消息
            enhanced_message = f"""参考文档：
{context}

用户问题：{input_text}

请基于以上参考文档回答用户问题。如果文档中没有相关信息，请诚实告知。"""
            await self.memory.add_user_message(enhanced_message)
        else:
            logger.warning(f"[UnityAgent] RAG 检索失败: {tool_result.error}")

        # 2. 调用 LLM
        context = await self.memory.get_context()
        response = await self.llm.chat(
            messages=context,
            system=self.memory.system_prompt,
            **kwargs
        )

        # 3. 添加助手回复到记忆
        await self.memory.add_assistant_message(response.content)
        return response.content

    async def run_stream(self, input_text: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式运行 Agent
        """
        # 添加用户消息到记忆
        await self.memory.add_user_message(input_text)

        # 1. RAG 检索
        yield json.dumps({"type": "status", "content": "正在检索知识库..."}, ensure_ascii=False)
        await asyncio.sleep(0)

        tool_result = await self.execute_tool("rag_search", knowledge_base=self.knowledge_base, query=input_text, top_k=5)

        if tool_result.success and tool_result.result.get("documents"):
            documents = tool_result.result["documents"]
            context = self._build_context(documents)

            enhanced_message = f"""参考文档：
{context}

用户问题：{input_text}

请基于以上参考文档回答用户问题。如果文档中没有相关信息，请诚实告知。"""
            await self.memory.add_user_message(enhanced_message)

            doc_count = len(documents)
            yield json.dumps(
                {"type": "status", "content": f"检索到 {doc_count} 条相关文档，正在生成回答..."},
                ensure_ascii=False
            )
        else:
            yield json.dumps({"type": "status", "content": "未检索到相关文档，直接回答..."}, ensure_ascii=False)
            logger.warning(f"[UnityAgent] RAG 检索失败: {tool_result.error}")

        await asyncio.sleep(0)

        # 2. 流式调用 LLM
        context = await self.memory.get_context()
        full_response = ""
        async for chunk in self.llm.chat_stream(
            messages=context,
            system=self.memory.system_prompt,
            **kwargs
        ):
            full_response += chunk
            yield chunk

        await self.memory.add_assistant_message(full_response)
