"""
Milvus 向量存储客户端
"""

from typing import List, Dict, Any

from core.config import settings
from core.logger import logger

vectorstore_logger = logger.bind(category="vectorstore")


class VectorStore:
    """Milvus 向量存储客户端"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._connected = False

    def _ensure_connected(self):
        if not self._connected:
            from pymilvus import connections
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port,
            )
            self._connected = True
            vectorstore_logger.info(
                f"Milvus 已连接: {settings.milvus_host}:{settings.milvus_port}"
            )

    async def search(
        self,
        query_embedding: List[float],
        collection_name: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        在指定 collection 中搜索相似向量

        Args:
            query_embedding: 查询向量
            collection_name: 集合名
            top_k: 返回条数
        """
        from pymilvus import Collection

        self._ensure_connected()

        try:
            collection = Collection(collection_name)
            collection.load()

            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16},
            }

            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text"],
            )

            items = []
            if results and results[0]:
                for hit in results[0]:
                    item = {
                        "text": hit.entity.get("text", ""),
                        "score": hit.score,
                    }
                    items.append(item)

            vectorstore_logger.info(
                f"Milvus 搜索完成: collection={collection_name}, "
                f"top_k={top_k}, 返回 {len(items)} 条"
            )
            return items

        except Exception as e:
            vectorstore_logger.error(f"Milvus 搜索失败: {e}")
            raise


# 全局实例
vectorstore = VectorStore()
