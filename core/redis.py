"""
Redis 客户端模块
提供异步 Redis 连接（延迟初始化单例）
"""

from core.config import settings
from core.logger import logger

_redis_client = None


async def get_redis():
    """获取 Redis 客户端（单例，延迟初始化）"""
    global _redis_client

    if _redis_client is None:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        logger.info(f"Redis 客户端已连接 | url={settings.redis_url}")

    return _redis_client


async def close_redis():
    """关闭 Redis 连接"""
    global _redis_client

    if _redis_client is not None:
        try:
            await _redis_client.close()
            logger.info("Redis 连接已关闭")
        except Exception as e:
            logger.warning(f"关闭 Redis 连接异常: {e}")
        finally:
            _redis_client = None
