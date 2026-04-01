"""
长期记忆管理模块
负责记忆的检索、提取（LLM分析）和存储（Milvus + MySQL）
"""

import json
import time
from typing import List, Dict, Any, Optional

from core.config import settings
from core.logger import logger
from core.vectorstore import vectorstore
from core.embedding import embedding_client
from core.llm import LLMClient, Message

ltm_logger = logger.bind(category="long_term_memory")

# LLM 记忆提取提示词
EXTRACTION_PROMPT = """你是一个信息提取助手。请分析以下用户与AI助手的对话，从中提取值得长期记住的信息。

提取规则：
1. 只提取真正有价值、跨对话仍然有意义的信息
2. 忽略临时性、一次性的信息（如"帮我查一下今天的天气"）
3. 重点关注：用户偏好、个人事实（姓名/职业/位置等）、重要上下文、明确指令
4. 如果没有值得记住的信息，返回空列表

请严格按以下 JSON 格式返回，不要包含其他内容：
{"memories": [{"text": "记忆内容描述", "category": "preference", "importance": 4}]}

category 可选值：
- preference: 用户偏好（如投资风格、技术偏好）
- fact: 用户个人事实（如姓名、职业、持仓信息）
- context: 重要上下文（如正在做的项目、之前的讨论背景）
- instruction: 用户明确给出的指令（如"以后回答用中文"）

importance 取值 1-5：
- 1-2: 低优先级，可能很快过时
- 3: 一般优先级
- 4-5: 高优先级，长期有价值

用户消息：
{user_message}

助手回复：
{assistant_message}"""


class LongTermMemoryManager:
    """长期记忆管理器"""

    COLLECTION_NAME = "agent_long_term_memory"

    def __init__(self):
        self._collection_ready = False
        self._llm = LLMClient()

    async def ensure_collection(self) -> bool:
        """幂等创建长期记忆 collection"""
        if self._collection_ready:
            return True

        success = vectorstore.create_collection(self.COLLECTION_NAME)
        if success:
            self._collection_ready = True
            ltm_logger.info("长期记忆 collection 已就绪")
        else:
            ltm_logger.error("长期记忆 collection 创建失败")
        return success

    async def retrieve(
        self,
        user_id: int,
        query: str,
        agent_name: Optional[str] = None,
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        检索与用户查询相关的长期记忆

        Args:
            user_id: 用户ID
            query: 用户查询文本
            agent_name: Agent名称（可选，用于过滤）
            top_k: 返回条数（默认使用配置值）

        Returns:
            相关记忆列表 [{"text", "category", "importance", "created_at", "score"}, ...]
        """
        if not self._collection_ready:
            return []

        top_k = top_k or settings.ltm_max_memories

        try:
            # 向量化查询
            query_embedding = await embedding_client.embed_single(query)

            # 构建过滤表达式
            filter_parts = [f"user_id == {user_id}"]
            if agent_name:
                filter_parts.append(f'agent_name == "{agent_name}"')
            filter_expr = " && ".join(filter_parts)

            # 搜索
            results = await vectorstore.search(
                query_embedding=query_embedding,
                collection_name=self.COLLECTION_NAME,
                top_k=top_k,
                filter_expr=filter_expr,
                output_fields=["text", "category", "importance", "created_at", "agent_name"],
            )

            ltm_logger.info(
                f"记忆检索完成 | user_id={user_id} | "
                f"query='{query[:30]}...' | 返回 {len(results)} 条"
            )
            return results

        except Exception as e:
            ltm_logger.error(f"记忆检索失败: {e}")
            return []

    async def extract_and_store(
        self,
        user_id: int,
        user_message: str,
        assistant_message: str,
        agent_name: str,
        conversation_id: str,
    ) -> int:
        """
        使用 LLM 从对话中提取有价值的记忆并存储

        Args:
            user_id: 用户ID
            user_message: 用户消息
            assistant_message: 助手回复
            agent_name: Agent名称
            conversation_id: 对话ID

        Returns:
            提取并存储的记忆条数
        """
        if not self._collection_ready:
            return 0

        try:
            # 调用 LLM 提取记忆
            prompt = EXTRACTION_PROMPT.format(
                user_message=user_message[:1000],
                assistant_message=assistant_message[:1000],
            )

            response = await self._llm.chat(
                messages=[Message(role="user", content=prompt)],
                max_tokens=settings.ltm_extraction_max_tokens,
                temperature=0.1,
            )

            # 解析 JSON 响应
            content = response.content.strip()
            # 处理可能的 markdown 代码块包裹
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            result = json.loads(content)
            memories = result.get("memories", [])

            if not memories:
                ltm_logger.info("本次对话无有价值信息需要记忆")
                return 0

            # 存储记忆
            stored_count = await self._store_memories(
                user_id=user_id,
                memories=memories,
                agent_name=agent_name,
                conversation_id=conversation_id,
            )

            ltm_logger.info(
                f"记忆提取完成 | user_id={user_id} | "
                f"提取 {len(memories)} 条, 存储 {stored_count} 条"
            )
            return stored_count

        except json.JSONDecodeError as e:
            ltm_logger.warning(f"记忆提取 JSON 解析失败: {e} | content={response.content[:200]}")
            return 0
        except Exception as e:
            ltm_logger.error(f"记忆提取失败: {e}")
            return 0

    async def _store_memories(
        self,
        user_id: int,
        memories: List[Dict[str, Any]],
        agent_name: str,
        conversation_id: str,
    ) -> int:
        """将提取的记忆存储到 Milvus 和 MySQL"""
        from api.models.user import get_session_factory
        from api.models.conversation import UserLongTermMemory

        if not memories:
            return 0

        now_ts = int(time.time())

        # 准备向量数据
        texts = [m["text"] for m in memories]
        embeddings = await embedding_client.embed(texts)

        # 准备 Milvus 插入数据
        milvus_data = []
        for i, mem in enumerate(memories):
            milvus_data.append({
                "embedding": embeddings[i],
                "text": mem["text"][:2000],
                "user_id": user_id,
                "agent_name": agent_name,
                "category": mem.get("category", "context"),
                "importance": min(max(int(mem.get("importance", 3)), 1), 5),
                "created_at": now_ts,
                "conversation_id": conversation_id,
            })

        # 插入 Milvus
        milvus_ids = await vectorstore.insert(self.COLLECTION_NAME, milvus_data)

        # 插入 MySQL 元数据
        factory = get_session_factory()
        if factory is None:
            ltm_logger.warning("数据库未初始化，跳过记忆元数据存储")
            return len(milvus_ids)

        stored = 0
        async with factory() as session:
            for i, mem in enumerate(memories):
                try:
                    db_mem = UserLongTermMemory(
                        user_id=user_id,
                        milvus_id=milvus_ids[i],
                        text=mem["text"][:2000],
                        category=mem.get("category", "context"),
                        importance=min(max(int(mem.get("importance", 3)), 1), 5),
                        agent_name=agent_name,
                        conversation_id=conversation_id,
                    )
                    session.add(db_mem)
                    stored += 1
                except Exception as e:
                    ltm_logger.error(f"记忆元数据写入失败: {e}")

            await session.commit()

        return stored

    @staticmethod
    def format_memories_as_context(memories: List[Dict[str, Any]]) -> str:
        """
        将检索到的记忆格式化为系统消息上下文

        Args:
            memories: 记忆列表（来自 retrieve 方法）

        Returns:
            格式化的上下文字符串
        """
        if not memories:
            return ""

        category_labels = {
            "preference": "偏好",
            "fact": "事实",
            "context": "上下文",
            "instruction": "指令",
        }

        lines = ["[用户长期记忆]"]
        for mem in memories:
            category = mem.get("category", "context")
            label = category_labels.get(category, category)
            text = mem.get("text", "")
            lines.append(f"- [{label}] {text}")

        return "\n".join(lines)

    async def delete_memory(self, milvus_id: int) -> bool:
        """删除单条记忆（Milvus）"""
        return await vectorstore.delete_by_ids(self.COLLECTION_NAME, [milvus_id])

    async def delete_memories(self, milvus_ids: List[int]) -> bool:
        """批量删除记忆（Milvus）"""
        return await vectorstore.delete_by_ids(self.COLLECTION_NAME, milvus_ids)


# 全局实例
long_term_memory_manager = LongTermMemoryManager()
