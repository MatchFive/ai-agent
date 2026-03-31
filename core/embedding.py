"""
Embedding 客户端
使用 OpenAI 兼容接口调用 Embedding 模型
"""

from typing import List
from core.config import settings
from core.logger import logger

embedding_logger = logger.bind(category="embedding")


class EmbeddingClient:
    """Embedding 客户端"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
                base_url=settings.embedding_base_url,
                api_key=settings.embedding_api_key,
            )
        return self._client

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        client = self._get_client()

        all_embeddings = []
        batch_size = settings.embedding_batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embedding_logger.info(f"base_url:{client.base_url},model_name:{settings.embedding_model}")
                response = await client.embeddings.create(
                    input=batch,
                    model=settings.embedding_model,
                    timeout=30,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                embedding_logger.info(f"Embedding 批次 {i // batch_size + 1}: {len(batch)} 条文本")
            except Exception as e:
                embedding_logger.error(f"Embedding 调用失败: {e}")
                raise

        return all_embeddings

    async def embed_single(self, text: str) -> List[float]:
        """单条文本转向量"""
        results = await self.embed([text])
        return results[0]


# 全局实例
embedding_client = EmbeddingClient()
