"""
新闻/热点查询工具
使用国内免费API数据源
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import json
import logging

# 配置logger
logger = logging.getLogger(__name__)


class HttpTool:
    """简化的HTTP工具类"""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def get(self, url: str, params: dict = None, headers: dict = None):
        """GET请求"""
        import httpx
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                try:
                    body = response.json()
                except:
                    body = response.text

                return {
                    "success": response.is_success,
                    "status_code": response.status_code,
                    "body": body
                }
            except Exception as e:
                logger.error(f"HTTP请求失败: {e}")
                return {"success": False, "error": str(e)}

    async def close(self):
        pass


class NewsTool:
    """
    新闻查询工具
    支持关键词搜索、分类新闻
    使用新浪财经/东方财富网数据源
    """

    def __init__(self):
        self.http_client = HttpTool(timeout=10.0)

    async def search_financial_news(
        self,
        query: str = "黄金 OR 股票 OR 投资 OR 财经",
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        搜索财经新闻

        Args:
            query: 搜索关键词（支持中文）
            page_size: 返回数量

        Returns:
            {
                "success": True,
                "articles": [
                    {
                        "title": "...",
                        "source": "新浪财经",
                        "url": "...",
                        "published_at": "2026-03-26T10:00:00Z",
                        "summary": "..."
                    }
                ]
            }
        """
        try:
            # 优先使用新浪财经
            result = await self._fetch_from_sina(query, page_size)
            if result.get("success"):
                return result

            # 备用：东方财富网
            result = await self._fetch_from_eastmoney(query, page_size)
            if result.get("success"):
                return result

            # 如果都失败，返回模拟数据
            return self._get_simulated_news()

        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _fetch_from_sina(
        self,
        query: str,
        page_size: int
    ) -> Dict[str, Any]:
        """从新浪财经获取新闻"""
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get"
            params = {
                "pageid": "153",
                "lid": "2516",
                "k": query,
                "num": page_size,
                "page": 1,
                "r": "0.1"
            }
            headers = {
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = await self.http_client.get(url, params=params, headers=headers)

            if response.get("success"):
                data = response.get("body", {})
                if isinstance(data, str):
                    data = json.loads(data)

                if data.get("result", {}).get("status", {}).get("code") == 0:
                    articles = []
                    for item in data.get("result", {}).get("data", []):
                        # 处理时间戳
                        published_at = ""
                        try:
                            ctime = item.get("ctime")
                            if ctime:
                                if isinstance(ctime, (int, float)):
                                    published_at = datetime.fromtimestamp(ctime).isoformat()
                                elif isinstance(ctime, str):
                                    published_at = ctime  # 如果已经是字符串，直接使用
                        except Exception as e:
                            logger.debug(f"解析时间失败: {e}")

                        articles.append({
                            "title": item.get("title", ""),
                            "source": item.get("media_name", "新浪财经"),
                            "url": item.get("url", ""),
                            "published_at": published_at,
                            "summary": item.get("intro", "")
                        })

                    if articles:
                        return {
                            "success": True,
                            "articles": articles,
                            "total": len(articles),
                            "source": "新浪财经"
                        }
        except Exception as e:
            logger.warning(f"新浪财经新闻 API failed: {e}")

        return {"success": False}

    async def _fetch_from_eastmoney(
        self,
        query: str,
        page_size: int
    ) -> Dict[str, Any]:
        """从东方财富网获取新闻"""
        try:
            url = "https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch"
            params = {
                "keyword": query,
                "type": "news",
                "pi": 1,
                "ps": page_size,
                "client": "web"
            }
            headers = {
                "Referer": "https://www.eastmoney.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = await self.http_client.get(url, params=params, headers=headers)

            if response.get("success"):
                data = response.get("body", {})
                if isinstance(data, str):
                    data = json.loads(data)

                if data.get("Data", {}).get("News"):
                    articles = []
                    for item in data["Data"]["News"]:
                        articles.append({
                            "title": item.get("Title", ""),
                            "source": item.get("Source", "东方财富网"),
                            "url": item.get("Url", ""),
                            "published_at": item.get("ShowTime", ""),
                            "summary": item.get("Abstract", "")
                        })

                    if articles:
                        return {
                            "success": True,
                            "articles": articles,
                            "total": len(articles),
                            "source": "东方财富网"
                        }
        except Exception as e:
            logger.warning(f"东方财富网新闻 API failed: {e}")

        return {"success": False}

    def _get_simulated_news(self) -> Dict[str, Any]:
        """模拟新闻数据（仅用于测试）"""
        simulated_articles = [
            {
                "title": "国际金价上涨，避险情绪升温",
                "source": "新浪财经",
                "url": "https://finance.sina.com.cn/news/1",
                "published_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "summary": "受市场不确定性影响，投资者转向避险资产，国际金价今日上涨..."
            },
            {
                "title": "央行释放宽松信号，A股市场迎来反弹",
                "source": "东方财富网",
                "url": "https://www.eastmoney.com/news/2",
                "published_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "summary": "中国人民银行释放货币政策宽松信号，A股市场今日大幅反弹..."
            },
            {
                "title": "科技股集体走强，人工智能概念股持续活跃",
                "source": "证券时报",
                "url": "https://www.stcn.com/news/3",
                "published_at": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
                "summary": "人工智能产业持续升温，相关概念股今日表现亮眼..."
            },
            {
                "title": "中国制造业PMI回升，经济复苏势头良好",
                "source": "第一财经",
                "url": "https://www.yicai.com/news/4",
                "published_at": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                "summary": "最新数据显示，中国制造业PMI指数回升至荣枯线以上..."
            },
            {
                "title": "新能源板块走强，锂电池产业链获资金追捧",
                "source": "中国证券报",
                "url": "https://www.cs.com.cn/news/5",
                "published_at": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                "summary": "新能源汽车销量持续增长，锂电池产业链迎来投资机会..."
            }
        ]

        return {
            "success": True,
            "articles": simulated_articles,
            "total": len(simulated_articles),
            "source": "Simulated",
            "note": "模拟数据，请检查网络连接获取实时新闻"
        }

    async def search_by_topic(
        self,
        topic: str,
        page_size: int = 5
    ) -> Dict[str, Any]:
        """
        按主题搜索新闻

        Args:
            topic: 主题 (黄金, 股票, 加密货币, 经济, 中国)
            page_size: 返回数量
        """
        topic_queries = {
            "黄金": "黄金 价格 贵金属",
            "股票": "股票 市场 交易",
            "加密货币": "比特币 数字货币 区块链",
            "经济": "经济 通胀 GDP 央行",
            "中国": "中国 经济 贸易 政策"
        }

        query = topic_queries.get(topic, topic)
        return await self.search_financial_news(query, page_size)

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.close()
