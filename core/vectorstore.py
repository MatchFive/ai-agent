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

    # 长期记忆 collection schema
    LTM_COLLECTION_NAME = "agent_long_term_memory"
    LTM_FIELDS = None  # 延迟初始化，需要 pymilvus

    def _get_ltm_fields(self):
        """延迟获取长期记忆 collection 的字段定义"""
        if self.LTM_FIELDS is None:
            from pymilvus import FieldSchema, DataType
            VectorStore.LTM_FIELDS = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.milvus_dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="user_id", dtype=DataType.INT64),
                FieldSchema(name="agent_name", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="importance", dtype=DataType.INT8),
                FieldSchema(name="created_at", dtype=DataType.INT64),
                FieldSchema(name="conversation_id", dtype=DataType.VARCHAR, max_length=36),
            ]
        return self.LTM_FIELDS

    def create_collection(
        self,
        collection_name: str,
        dim: int = None,
        fields_schema: list = None,
    ) -> bool:
        """
        创建 Milvus collection（幂等操作）

        Args:
            collection_name: 集合名
            dim: 向量维度（仅当 fields_schema 为 None 时使用）
            fields_schema: 自定义字段列表，为 None 时使用长期记忆默认 schema
        """
        from pymilvus import Collection, FieldSchema, DataType, CollectionSchema

        self._ensure_connected()

        try:
            from pymilvus import utility
            if utility.has_collection(collection_name):
                vectorstore_logger.info(f"Collection '{collection_name}' 已存在，跳过创建")
                return True
        except Exception as e:
            vectorstore_logger.warning(f"检查 collection 存在性失败: {e}")

        try:
            if fields_schema:
                fields = fields_schema
            else:
                fields = self._get_ltm_fields()

            schema = CollectionSchema(fields=fields, description="AI Agent 长期记忆")
            collection = Collection(name=collection_name, schema=schema)

            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            collection.create_index(field_name="embedding", index_params=index_params)

            vectorstore_logger.info(f"Collection '{collection_name}' 创建成功")
            return True
        except Exception as e:
            vectorstore_logger.error(f"创建 collection '{collection_name}' 失败: {e}")
            return False

    async def insert(
        self,
        collection_name: str,
        data: List[Dict[str, Any]],
    ) -> List[int]:
        """
        批量插入向量数据

        Args:
            collection_name: 集合名
            data: 数据列表，每项包含 embedding, text, user_id, agent_name,
                  category, importance, created_at, conversation_id

        Returns:
            插入的 ID 列表
        """
        from pymilvus import Collection

        self._ensure_connected()

        try:
            collection = Collection(collection_name)
            collection.load()

            # 按字段组织数据
            insert_data = {
                "embedding": [item["embedding"] for item in data],
                "text": [item["text"] for item in data],
                "user_id": [item["user_id"] for item in data],
                "agent_name": [item["agent_name"] for item in data],
                "category": [item["category"] for item in data],
                "importance": [item["importance"] for item in data],
                "created_at": [item["created_at"] for item in data],
                "conversation_id": [item["conversation_id"] for item in data],
            }

            result = collection.insert(insert_data)
            collection.flush()

            inserted_ids = result.primary_keys
            vectorstore_logger.info(
                f"Milvus 插入完成: collection={collection_name}, "
                f"插入 {len(inserted_ids)} 条"
            )
            return inserted_ids

        except Exception as e:
            vectorstore_logger.error(f"Milvus 插入失败: {e}")
            raise

    async def delete_by_ids(
        self,
        collection_name: str,
        ids: List[int],
    ) -> bool:
        """
        按 ID 删除记录

        Args:
            collection_name: 集合名
            ids: 要删除的 ID 列表
        """
        from pymilvus import Collection

        self._ensure_connected()

        try:
            collection = Collection(collection_name)
            collection.load()
            collection.delete(expr=f"id in {ids}")
            collection.flush()

            vectorstore_logger.info(
                f"Milvus 删除完成: collection={collection_name}, 删除 {len(ids)} 条"
            )
            return True
        except Exception as e:
            vectorstore_logger.error(f"Milvus 删除失败: {e}")
            raise

    async def search(
        self,
        query_embedding: List[float],
        collection_name: str,
        top_k: int = 5,
        filter_expr: str = None,
        output_fields: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        在指定 collection 中搜索相似向量

        Args:
            query_embedding: 查询向量
            collection_name: 集合名
            top_k: 返回条数
            filter_expr: 过滤表达式（如 "user_id == 123"）
            output_fields: 返回字段列表（默认 ["text"]）
        """
        from pymilvus import Collection

        self._ensure_connected()

        if output_fields is None:
            output_fields = ["text"]

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
                expr=filter_expr,
                output_fields=output_fields,
            )

            items = []
            if results and results[0]:
                for hit in results[0]:
                    item = {"score": hit.score}
                    for field in output_fields:
                        item[field] = hit.entity.get(field, "")
                    items.append(item)

            vectorstore_logger.info(
                f"Milvus 搜索完成: collection={collection_name}, "
                f"top_k={top_k}, filter={filter_expr}, 返回 {len(items)} 条"
            )
            return items

        except Exception as e:
            vectorstore_logger.error(f"Milvus 搜索失败: {e}")
            raise


# 全局实例
vectorstore = VectorStore()
