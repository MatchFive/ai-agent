"""
RAG 知识库检索工具
"""

from typing import Dict, Any

from core.logger import logger
from tools.registry import register_tool

tool_logger = logger.bind(category="tool")


@register_tool(
    name="rag_search",
    description="搜索指定知识库，返回与查询最相关的文档片段。参数 knowledge_base 为知识库名称。",
    parameters={
        "type": "object",
        "properties": {
            "knowledge_base": {
                "type": "string",
                "description": "知识库名称（如 'Unity手册'）"
            },
            "query": {
                "type": "string",
                "description": "搜索查询内容"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量，默认5",
                "default": 5
            }
        },
        "required": ["knowledge_base", "query"]
    },
    category="rag",
    method_name="search"
)
class RAGSearchTool:
    """RAG 知识库检索工具"""

    async def search(self, knowledge_base: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        搜索知识库

        Args:
            knowledge_base: 知识库名称
            query: 查询文本
            top_k: 返回条数
        """
        tool_logger.info(f"[RAG搜索] kb={knowledge_base}, query={query}, top_k={top_k}")

        try:
            # 1. 根据知识库名查询 collection_name
            collection_name = await self._get_collection_name(knowledge_base)
            if not collection_name:
                return {
                    "success": False,
                    "query": query,
                    "error": f"知识库 '{knowledge_base}' 未找到或已禁用",
                    "documents": [],
                    "total": 0
                }

            # 2. 文本转向量
            from core.embedding import embedding_client
            query_embedding = await embedding_client.embed_single(query)

            # 3. Milvus 向量搜索
            from core.vectorstore import vectorstore
            results = await vectorstore.search(query_embedding, collection_name=collection_name, top_k=top_k)

            # 4. 格式化结果
            documents = []
            for i, item in enumerate(results):
                documents.append({
                    "index": i + 1,
                    "text": item["text"],
                    "score": round(item["score"], 4),
                })

            tool_logger.info(
                f"[RAG搜索] 完成 | kb={knowledge_base} collection={collection_name} | "
                f"返回 {len(documents)} 条结果"
            )

            return {
                "success": True,
                "knowledge_base": knowledge_base,
                "query": query,
                "documents": documents,
                "total": len(documents)
            }

        except Exception as e:
            tool_logger.error(f"[RAG搜索] 失败: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "documents": [],
                "total": 0
            }

    @staticmethod
    async def _get_collection_name(knowledge_base: str) -> str | None:
        """根据知识库名查询 Milvus collection_name"""
        from api.models.user import get_session_factory
        from api.models.agent_config import KnowledgeBase
        from sqlalchemy import select

        factory = get_session_factory()
        if factory is None:
            return None

        try:
            async with factory() as session:
                result = await session.execute(
                    select(KnowledgeBase.collection_name).where(
                        KnowledgeBase.name == knowledge_base,
                        KnowledgeBase.is_active == True
                    )
                row = result.scalar_one_or_none()
                return row if row else None
        except Exception:
            return None
