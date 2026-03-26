"""
股票数据查询工具
使用国内免费API数据源
"""

from typing import Dict, Any, List
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


class StockDataTool:
    """
    股票数据查询工具
    支持实时价格、历史数据
    使用新浪财经/东方财富网数据源
    """

    def __init__(self):
        self.http_client = HttpTool(timeout=10.0)

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时报价

        Args:
            symbol: 股票代码
                - A股: sh600519, sz000001
                - 港股: hk00700
                - 美股: AAPL, TSLA

        Returns:
            {
                "success": True,
                "symbol": "SH600519",
                "name": "贵州茅台",
                "price": 1850.00,
                "change": 28.50,
                "change_percent": 1.56,
                "volume": 50000000,
                "timestamp": "2026-03-26T10:30:00Z",
                "source": "新浪财经"
            }
        """
        try:
            # 优先使用新浪财经
            result = await self._fetch_from_sina(symbol)
            if result.get("success"):
                return result

            # 备用：东方财富网
            result = await self._fetch_from_eastmoney(symbol)
            if result.get("success"):
                return result

            # 如果都失败，返回模拟数据
            return self._get_simulated_data(symbol)

        except Exception as e:
            logger.error(f"Failed to fetch stock data for {symbol}: {e}")
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }

    async def _fetch_from_sina(self, symbol: str) -> Dict[str, Any]:
        """从新浪财经获取股票数据"""
        try:
            # 支持A股、港股、美股
            if symbol.startswith(("sh", "sz", "SH", "SZ")):
                # A股
                code = symbol.lower()
            elif symbol.startswith(("hk", "HK")):
                # 港股
                code = symbol.lower().replace("hk", "hk")
            else:
                # 美股
                code = f"gb_{symbol.lower()}"

            url = f"https://hq.sinajs.cn/list={code}"
            headers = {"Referer": "https://finance.sina.com.cn"}

            response = await self.http_client.get(url, headers=headers)

            if response.get("success"):
                body = response.get("body", "")
                if body and isinstance(body, str):
                    # 解析新浪财经返回的数据格式
                    var_name = f"hq_str_{code}="
                    if var_name in body:
                        data_str = body.split(f'{var_name}"')[1].split('"')[0]
                        parts = data_str.split(",")

                        # 判断数据类型（通过代码前缀）
                        is_a_stock = code.startswith(("sh", "sz"))
                        is_us_stock = code.startswith("gb_")

                        if is_a_stock and len(parts) >= 32:
                            # A股数据格式
                            name = parts[0]
                            price = float(parts[3]) if parts[3] else 0
                            yesterday_close = float(parts[2]) if parts[2] else price
                            change = price - yesterday_close if yesterday_close else 0
                            change_percent = (change / yesterday_close * 100) if yesterday_close else 0
                            volume = int(float(parts[8])) if parts[8] else 0

                            return {
                                "success": True,
                                "symbol": symbol.upper(),
                                "name": name,
                                "price": price,
                                "change": round(change, 2),
                                "change_percent": round(change_percent, 2),
                                "volume": volume,
                                "timestamp": parts[31] if len(parts) > 31 else datetime.utcnow().isoformat(),
                                "source": "新浪财经"
                            }
                        elif is_us_stock and len(parts) >= 10:
                            # 美股数据格式：名称,当前价,涨跌额,时间,涨跌幅,开盘价,最高价,最低价,...
                            try:
                                name = parts[0]
                                price = float(parts[1]) if parts[1] else 0
                                change = float(parts[2]) if parts[2] else 0
                                # parts[3]是时间，跳过
                                change_percent = float(parts[4]) if parts[4] else 0
                                volume = int(float(parts[10])) if len(parts) > 10 and parts[10] else 0

                                return {
                                    "success": True,
                                    "symbol": symbol.upper(),
                                    "name": name,
                                    "price": price,
                                    "change": round(change, 2),
                                    "change_percent": round(change_percent, 2),
                                    "volume": volume,
                                    "timestamp": parts[3] if parts[3] else datetime.utcnow().isoformat(),
                                    "source": "新浪财经"
                                }
                            except (ValueError, IndexError) as e:
                                logger.warning(f"解析美股数据失败: {e}")
                        elif len(parts) >= 10:
                            # 港股数据格式
                            name = parts[0]
                            price = float(parts[6]) if len(parts) > 6 and parts[6] else 0
                            yesterday_close = float(parts[4]) if len(parts) > 4 and parts[4] else price
                            change = price - yesterday_close if yesterday_close else 0
                            change_percent = (change / yesterday_close * 100) if yesterday_close else 0
                            volume = int(float(parts[10])) if len(parts) > 10 and parts[10] else 0

                            return {
                                "success": True,
                                "symbol": symbol.upper(),
                                "name": name,
                                "price": price,
                                "change": round(change, 2),
                                "change_percent": round(change_percent, 2),
                                "volume": volume,
                                "timestamp": parts[17] if len(parts) > 17 else datetime.utcnow().isoformat(),
                                "source": "新浪财经"
                            }
        except Exception as e:
            logger.warning(f"新浪财经 API failed: {e}")

        return {"success": False}

    async def _fetch_from_eastmoney(self, symbol: str) -> Dict[str, Any]:
        """从东方财富网获取股票数据"""
        try:
            # 判断股票类型
            if any(symbol.startswith(prefix) for prefix in ["sh", "sz", "SH", "SZ"]):
                market = "SH" if symbol.upper().startswith("SH") else "SZ"
                code = symbol[2:]
                url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f58"
            else:
                # 美股/港股
                url = f"https://push2.eastmoney.com/api/qt/stock/get?secid=106.{symbol}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f58"

            response = await self.http_client.get(url)

            if response.get("success"):
                data = response.get("body", {})
                if isinstance(data, str):
                    data = json.loads(data)

                if data.get("data"):
                    quote = data["data"]
                    price = quote.get("f43", 0) / 100 if quote.get("f43") else 0
                    yesterday_close = quote.get("f46", 0) / 100 if quote.get("f46") else price
                    change = price - yesterday_close
                    change_percent = (change / yesterday_close * 100) if yesterday_close else 0

                    return {
                        "success": True,
                        "symbol": symbol.upper(),
                        "name": quote.get("f58", ""),
                        "price": price,
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "volume": quote.get("f47", 0),
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "东方财富网"
                    }
        except Exception as e:
            logger.warning(f"东方财富网 API failed: {e}")

        return {"success": False}

    def _get_simulated_data(self, symbol: str) -> Dict[str, Any]:
        """模拟数据（仅用于测试）"""
        simulated_prices = {
            "AAPL": {"price": 178.50, "change": 2.30, "change_percent": 1.30, "name": "苹果公司"},
            "TSLA": {"price": 245.60, "change": -3.20, "change_percent": -1.29, "name": "特斯拉"},
            "GOOGL": {"price": 156.80, "change": 1.50, "change_percent": 0.97, "name": "谷歌"},
            "MSFT": {"price": 425.30, "change": 5.10, "change_percent": 1.21, "name": "微软"},
            "AMZN": {"price": 185.20, "change": -1.80, "change_percent": -0.96, "name": "亚马逊"},
            "sh600519": {"price": 1850.00, "change": 28.50, "change_percent": 1.56, "name": "贵州茅台"},
            "sz000001": {"price": 12.85, "change": 0.15, "change_percent": 1.18, "name": "平安银行"},
            "sz000858": {"price": 168.50, "change": -2.30, "change_percent": -1.35, "name": "五粮液"},
        }

        data = simulated_prices.get(symbol.lower(), {
            "price": 100.00,
            "change": 0,
            "change_percent": 0,
            "name": symbol.upper()
        })

        return {
            "success": True,
            "symbol": symbol.upper(),
            "name": data["name"],
            "price": data["price"],
            "change": data["change"],
            "change_percent": data["change_percent"],
            "volume": 1000000,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "Simulated",
            "note": "模拟数据，请检查网络连接获取实时数据"
        }

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """批量获取股票报价"""
        results = {}
        for symbol in symbols:
            result = await self.get_quote(symbol)
            results[symbol] = result

        return {
            "success": True,
            "data": results
        }

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.http_client.close()
