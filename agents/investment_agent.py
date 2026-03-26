"""
投资理财分析 Agent
"""

from typing import Optional, AsyncGenerator
import json

from agents.base import BaseAgent, Tool
from core.llm import LLMClient
from core.memory import Memory
from core.logger import logger
from tools.gold_price_tool import GoldPriceTool
from tools.stock_data_tool import StockDataTool
from tools.news_tool import NewsTool


class InvestmentAgent(BaseAgent):
    """
    投资理财分析 Agent

    功能:
    - 分析黄金走势
    - 分析股票走势
    - 结合新闻/政策分析
    - 提供投资建议
    """

    def __init__(
        self,
        name: str = "InvestmentAgent",
        description: str = "投资理财分析助手，提供黄金、股票市场分析和投资建议",
        llm_client: Optional[LLMClient] = None,
        memory: Optional[Memory] = None,
        **kwargs
    ):
        # 系统提示词
        system_prompt = """你是一位专业的投资理财分析助手。你的职责是：

1. **市场分析**: 分析黄金、股票等金融产品的走势
2. **新闻解读**: 结合最新的财经新闻和政策动态
3. **风险评估**: 提供客观的风险提示
4. **投资建议**: 基于数据分析给出专业的投资建议

**可用工具**:
- get_gold_price: 获取当前黄金价格（美元/盎司）
- get_stock_quote: 获取股票实时报价，参数: symbol（股票代码）
- search_news: 搜索财经新闻，参数: query（搜索关键词，可选）

**工作流程**:
- 当用户询问黄金价格时，使用 get_gold_price 工具获取实时数据
- 当用户询问股票时，使用 get_stock_quote 工具获取股票信息
- 当需要了解市场动态时，使用 search_news 工具获取财经新闻
- 综合分析数据后，给出专业、客观的分析报告

**注意事项**:
- 始终基于数据说话，不要凭空猜测
- 明确提示投资有风险
- 不做绝对性的价格预测
- 提供多元化视角的分析
- 回复使用中文

请始终以专业、客观、负责任的态度为用户提供服务。"""

        # 初始化基类
        super().__init__(
            name=name,
            description=description,
            llm_client=llm_client,
            memory=memory,
            system_prompt=system_prompt,
            **kwargs
        )

        # 初始化工具实例
        self.gold_tool = GoldPriceTool()
        self.stock_tool = StockDataTool()
        self.news_tool = NewsTool()

        # 注册工具
        self._register_tools()

    def _register_tools(self):
        """注册投资分析工具"""

        # 黄金价格工具
        gold_tool = Tool(
            name="get_gold_price",
            description="获取当前黄金价格（美元/盎司），无需参数",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._handle_gold_price
        )
        self.register_tool(gold_tool)

        # 股票查询工具
        stock_tool = Tool(
            name="get_stock_quote",
            description="获取股票实时报价。参数: symbol (股票代码，如 AAPL, TSLA)",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码，如 AAPL, TSLA, GOOGL"
                    }
                },
                "required": ["symbol"]
            },
            handler=self._handle_stock_quote
        )
        self.register_tool(stock_tool)

        # 新闻搜索工具
        news_tool = Tool(
            name="search_news",
            description="搜索财经新闻。参数: query (搜索关键词，可选，默认为金融相关)",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如 'gold', 'stock', 'china economy'"
                    }
                },
                "required": []
            },
            handler=self._handle_news_search
        )
        self.register_tool(news_tool)

    async def _handle_gold_price(self, **kwargs) -> dict:
        """处理黄金价格查询"""
        result = await self.gold_tool.get_current_price()
        return result

    async def _handle_stock_quote(self, symbol: str, **kwargs) -> dict:
        """处理股票查询"""
        result = await self.stock_tool.get_quote(symbol)
        return result

    async def _handle_news_search(self, query: str = "gold OR stock OR investment", **kwargs) -> dict:
        """处理新闻搜索"""
        result = await self.news_tool.search_financial_news(query=query)
        return result

    async def run(self, input_text: str, **kwargs) -> str:
        """
        运行 Agent（非流式）

        实现思路:
        1. 添加用户消息到记忆
        2. 获取对话上下文
        3. 调用 LLM 生成响应
        4. 检测是否需要调用工具
        5. 如果需要，执行工具并将结果反馈给 LLM
        6. 返回最终响应
        """
        # 添加用户消息到记忆
        await self.memory.add_user_message(input_text)

        # 获取对话上下文
        context = await self.memory.get_context()

        # 第一次调用 LLM
        llm_response = await self.llm.chat(
            messages=context,
            system=self.memory.system_prompt,
            **kwargs
        )

        response_text = llm_response.content

        # 检测是否需要调用工具（简单的关键词检测）
        # 实际项目中应使用 LLM 的 function calling 功能
        tools_to_call = self._detect_tool_calls(input_text, response_text)

        if tools_to_call:
            for tool_name, tool_args in tools_to_call:
                # 执行工具
                tool_result = await self.execute_tool(tool_name, **tool_args)

                if tool_result.success:
                    # 将工具结果添加到上下文
                    tool_message = f"[工具 {tool_name} 执行结果]\n{json.dumps(tool_result.result, ensure_ascii=False, indent=2)}"
                    await self.memory.add_system_message(tool_message)
                else:
                    await self.memory.add_system_message(f"[工具 {tool_name} 执行失败] {tool_result.error}")

            # 重新获取上下文并调用 LLM 生成最终响应
            context = await self.memory.get_context()
            final_response = await self.llm.chat(
                messages=context,
                system=self.memory.system_prompt,
                **kwargs
            )
            response_text = final_response.content

        # 添加助手响应到记忆
        await self.memory.add_assistant_message(response_text)

        return response_text

    def _detect_tool_calls(self, user_input: str, llm_response: str) -> list:
        """
        检测需要调用的工具
        简单的关键词检测，实际应使用 function calling
        """
        calls = []
        user_lower = user_input.lower()

        # 检测黄金价格查询
        if any(kw in user_lower for kw in ["黄金", "gold", "金价", "贵金属"]):
            if "price" not in llm_response.lower() and "价格" not in llm_response:
                calls.append(("get_gold_price", {}))

        # 检测股票查询
        stock_keywords = {
            "苹果": "AAPL",
            "特斯拉": "TSLA",
            "谷歌": "GOOGL",
            "微软": "MSFT",
            "亚马逊": "AMZN",
            "英伟达": "NVDA",
            "腾讯": "TCEHY",
            "阿里": "BABA"
        }

        for keyword, symbol in stock_keywords.items():
            if keyword in user_input:
                calls.append(("get_stock_quote", {"symbol": symbol}))
                break

        # 如果输入包含股票代码格式
        import re
        stock_pattern = r'\b([A-Z]{1,5})\b'
        matches = re.findall(stock_pattern, user_input.upper())
        for match in matches:
            if match not in ["THE", "AND", "FOR", "API"]:
                calls.append(("get_stock_quote", {"symbol": match}))
                break

        # 检测新闻查询
        if any(kw in user_lower for kw in ["新闻", "news", "热点", "资讯", "动态", "政策"]):
            query = "gold OR stock OR investment"
            if "黄金" in user_lower or "gold" in user_lower:
                query = "gold price precious metals"
            elif "股票" in user_lower or "stock" in user_lower:
                query = "stock market trading"
            calls.append(("search_news", {"query": query}))

        return calls

    async def run_stream(
        self,
        input_text: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式运行 Agent
        """
        # 添加用户消息到记忆
        await self.memory.add_user_message(input_text)

        # 获取对话上下文
        context = await self.memory.get_context()

        # 检测是否需要调用工具
        tools_to_call = self._detect_tool_calls(input_text, "")

        # 如果需要调用工具，先执行工具
        if tools_to_call:
            for tool_name, tool_args in tools_to_call:
                tool_result = await self.execute_tool(tool_name, **tool_args)

                if tool_result.success:
                    tool_message = f"[工具 {tool_name} 执行结果]\n{json.dumps(tool_result.result, ensure_ascii=False, indent=2)}"
                    await self.memory.add_system_message(tool_message)
                else:
                    await self.memory.add_system_message(f"[工具 {tool_name} 执行失败] {tool_result.error}")

            # 更新上下文
            context = await self.memory.get_context()

        # 流式调用 LLM
        full_response = ""
        async for chunk in self.llm.chat_stream(
            messages=context,
            system=self.memory.system_prompt,
            **kwargs
        ):
            full_response += chunk
            yield chunk

        # 添加完整响应到记忆
        await self.memory.add_assistant_message(full_response)

    async def cleanup(self):
        """清理资源"""
        try:
            await self.gold_tool.close()
            await self.stock_tool.close()
            await self.news_tool.close()
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
