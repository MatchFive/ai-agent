"""
黄金价格查询工具
使用国内免费API数据源
"""

from typing import Dict, Any
from datetime import datetime
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


class GoldPriceTool:
    """
    黄金价格查询工具
    支持实时价格查询
    使用新浪财经/东方财富网数据源
    """

    def __init__(self):
        self.http_client = HttpTool(timeout=10.0)

    async def get_current_price(self) -> Dict[str, Any]:
        """
        获取当前黄金价格

        Returns:
            {
                "success": True,
                "price": 2000.50,
                "currency": "USD",
                "change": 5.20,
                "change_percent": 0.26,
                "timestamp": "2026-03-26T10:30:00Z",
                "source": "新浪财经"
            }
        """
        try:
            # 优先使用新浪财经
            result = await self._fetch_from_sina()
            if result.get("success"):
                return result

            # 备用：东方财富网
            result = await self._fetch_from_eastmoney()
            if result.get("success"):
                return result

            # 如果都失败，返回模拟数据
            return self._get_simulated_data()

        except Exception as e:
            logger.error(f"Failed to fetch gold price: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _fetch_from_sina(self) -> Dict[str, Any]:
        """从新浪财经获取黄金价格"""
        try:
            url = "https://hq.sinajs.cn/list=hf_GC"
            headers = {"Referer": "https://finance.sina.com.cn"}

            response = await self.http_client.get(url, headers=headers)

            if response.get("success"):
                body = response.get("body", "")
                if body and isinstance(body, str):
                    # 解析新浪财经返回的数据格式: var hq_str_hf_GC="价格,涨跌,涨跌幅,..."
                    if "hq_str_hf_GC=" in body:
                        data_str = body.split('hq_str_hf_GC="')[1].split('"')[0]
                        parts = data_str.split(",")

                        if len(parts) >= 6:
                            # 数据格式: 价格,,买价,卖价,最高价,最低价,时间,昨收价,...
                            try:
                                price = float(parts[0]) if parts[0] else 0
                                # 计算涨跌（当前价 - 昨收价）
                                yesterday_close = float(parts[7]) if len(parts) > 7 and parts[7] else price
                                change = price - yesterday_close
                                change_percent = (change / yesterday_close * 100) if yesterday_close else 0

                                return {
                                    "success": True,
                                    "price": price,
                                    "currency": "USD",
                                    "change": round(change, 2),
                                    "change_percent": round(change_percent, 2),
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "source": "新浪财经"
                                }
                            except (ValueError, IndexError) as e:
                                logger.warning(f"解析新浪财经数据失败: {e}")
        except Exception as e:
            logger.warning(f"新浪财经 API failed: {e}")

        return {"success": False}

    async def _fetch_from_eastmoney(self) -> Dict[str, Any]:
        """从东方财富网获取黄金价格"""
        try:
            url = "https://quote.eastmoney.com/center/api/price/quote/SHFE.AU"
            response = await self.http_client.get(url)

            if response.get("success"):
                data = response.get("body", {})
                if isinstance(data, str):
                    data = json.loads(data)

                if data.get("code") == 0 and data.get("data"):
                    quote = data["data"]
                    return {
                        "success": True,
                        "price": quote.get("price", 0),
                        "currency": "CNY",  # 东方财富返回人民币价格
                        "change": quote.get("change", 0),
                        "change_percent": quote.get("changePct", 0),
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "东方财富网"
                    }
        except Exception as e:
            logger.warning(f"东方财富网 API failed: {e}")

        return {"success": False}

    def _get_simulated_data(self) -> Dict[str, Any]:
        """模拟数据（仅用于测试）"""
        return {
            "success": True,
            "price": 2325.50,
            "currency": "USD",
            "change": 12.30,
            "change_percent": 0.53,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "Simulated",
            "note": "模拟数据，请检查网络连接获取实时数据"
        }

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.close()
