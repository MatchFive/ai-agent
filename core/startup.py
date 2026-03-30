"""
启动模块
负责工具扫描、DB同步、Agent加载
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from tools.registry import ToolRegistry, scan_classes_for_method_tools


def import_tools():
    """导入所有工具模块，触发装饰器注册"""
    import tools.gold_price_tool
    import tools.stock_data_tool
    import tools.news_tool
    import tools.email_tool
    import tools.file_tool
    import tools.http_tool
    import tools.scheduler_tool
    import tools.rag_tool

    # 收集方法级装饰器
    scan_classes_for_method_tools()

    logger.info(f"[Startup] 工具扫描完成，共注册 {len(ToolRegistry.get_all())} 个工具")


async def sync_tools_to_db():
    """
    将 ToolRegistry 中的工具同步到 tool_configs 表。
    - 新工具 → INSERT
    - version_hash 变更 → UPDATE
    - 管理员手动禁用的（is_active=False）不自动恢复
    """
    from api.models.user import get_session_factory
    from api.models.agent_config import ToolConfig

    factory = get_session_factory()
    if factory is None:
        logger.warning("[ToolSync] Session factory not ready, skipping")
        return

    async with factory() as session:
        registrations = ToolRegistry.get_all()
        inserted = 0
        updated = 0

        for name, reg in registrations.items():
            result = await session.execute(
                select(ToolConfig).where(ToolConfig.name == name)
            )
            db_tool = result.scalar_one_or_none()

            if db_tool is None:
                db_tool = ToolConfig(
                    name=reg.name,
                    description=reg.description,
                    parameters_json=json.dumps(reg.parameters, ensure_ascii=False),
                    handler_class=reg.handler_class_path,
                    handler_method=reg.handler_method,
                    category=reg.category,
                    version_hash=reg.version_hash,
                    is_active=True,
                )
                session.add(db_tool)
                inserted += 1
            elif db_tool.version_hash != reg.version_hash:
                db_tool.description = reg.description
                db_tool.parameters_json = json.dumps(reg.parameters, ensure_ascii=False)
                db_tool.handler_class = reg.handler_class_path
                db_tool.handler_method = reg.handler_method
                db_tool.category = reg.category
                db_tool.version_hash = reg.version_hash
                updated += 1

        await session.commit()
        logger.info(
            f"[ToolSync] 同步完成: {len(registrations)} 个工具, "
            f"新增 {inserted}, 更新 {updated}"
        )


async def seed_default_agents():
    """如果 DB 中没有默认数据，插入配置"""
    from api.models.user import get_session_factory
    from api.models.agent_config import AgentConfig, ToolConfig, AgentToolConfig, KnowledgeBase

    factory = get_session_factory()
    if factory is None:
        return

    async with factory() as session:
        # ---- 默认知识库 ----
        result = await session.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == "Unity手册")
        )
        if not result.scalar_one_or_none():
            await _seed_knowledge_base(session)
            logger.info("[Seed] 默认知识库 'Unity手册' 配置已创建")

        # ---- InvestmentAgent ----
        result = await session.execute(
            select(AgentConfig).where(AgentConfig.name == "InvestmentAgent")
        )
        if not result.scalar_one_or_none():
            await _seed_investment_agent(session)
            logger.info("[Seed] 默认 InvestmentAgent 配置已创建")

        # ---- UnityAgent ----
        result = await session.execute(
            select(AgentConfig).where(AgentConfig.name == "UnityAgent")
        )
        if not result.scalar_one_or_none():
            await _seed_unity_agent(session)
            logger.info("[Seed] 默认 UnityAgent 配置已创建")


async def _seed_knowledge_base(session):
    """种子数据：默认知识库"""
    from api.models.agent_config import KnowledgeBase

    kb = KnowledgeBase(
        name="Unity手册",
        description="Unity 2022.3 LTS 版本使用手册",
        collection_name="unity_docs_2022_3",
        embedding_dim=1024,
        is_active=True,
    )
    session.add(kb)


async def _seed_investment_agent(session):
    """种子数据：InvestmentAgent"""
    from api.models.agent_config import AgentConfig, ToolConfig, AgentToolConfig

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

**时间信息**: 每条用户消息开头会附带当前服务器时间（格式: [当前时间: YYYY-MM-DD HH:MM:SS 星期X]），请以此时间为准回答时间相关问题，不要猜测当前时间。

**注意事项**:
- 始终基于数据说话，不要凭空猜测
- 明确提示投资有风险
- 不做绝对性的价格预测
- 提供多元化视角的分析
- 回复使用中文

请始终以专业、客观、负责任的态度为用户提供服务。"""

    agent = AgentConfig(
        name="InvestmentAgent",
        description="投资理财分析助手，提供黄金、股票市场分析和投资建议",
        system_prompt=system_prompt,
        agent_class="agents.investment_agent.InvestmentAgent",
        is_active=True,
        config_json=json.dumps({"cache_ttl": 900}),
    )
    session.add(agent)
    await session.flush()

    for tool_name, sort_order in [
        ("get_gold_price", 0),
        ("get_stock_quote", 1),
        ("search_news", 2),
    ]:
        result = await session.execute(
            select(ToolConfig).where(ToolConfig.name == tool_name)
        )
        tool = result.scalar_one_or_none()
        if tool:
            session.add(AgentToolConfig(
                agent_id=agent.id,
                tool_id=tool.id,
                sort_order=sort_order,
            ))


async def _seed_unity_agent(session):
    """种子数据：UnityAgent"""
    from api.models.agent_config import AgentConfig, ToolConfig, AgentToolConfig

    system_prompt = """你是 Unity 入门小助手，专门帮助初学者学习 Unity 游戏引擎。

**你的知识来源**：
- 你可以访问 Unity 使用手册知识库
- 每次回答前，你会先从知识库中检索相关文档片段

**回答规范**：
1. 始终基于检索到的文档内容回答，不要凭空编造
2. 如果检索结果中没有相关信息，诚实告知用户并建议换个关键词
3. 回答要结构清晰、通俗易懂，适合初学者
4. 涉及代码的部分给出示例代码
5. 适当给出操作步骤指引
6. 回复使用中文

**注意事项**：
- 不要声称自己是官方文档，你是基于文档的 AI 助手
- 如果用户的问题与 Unity 无关，礼貌地告知你只回答 Unity 相关问题
- 保持耐心和友好的语气"""

    agent = AgentConfig(
        name="UnityAgent",
        description="Unity 入门小助手，基于 2022.3 版 Unity 使用手册提供学习指导",
        system_prompt=system_prompt,
        agent_class="agents.unity_agent.UnityAgent",
        is_active=True,
        config_json=json.dumps({"cache_ttl": 0, "knowledge_base": "Unity手册"}),
    )
    session.add(agent)
    await session.flush()

    result = await session.execute(
        select(ToolConfig).where(ToolConfig.name == "rag_search")
    )
    tool = result.scalar_one_or_none()
    if tool:
        session.add(AgentToolConfig(
            agent_id=agent.id,
            tool_id=tool.id,
            sort_order=0,
        ))


async def load_agents_from_db():
    """从 DB 加载所有活跃的 Agent 到内存"""
    from api.models.user import get_session_factory
    from api.models.agent_config import AgentConfig, AgentToolConfig, ToolConfig
    from agents.manager import agent_manager
    from agents.base import Tool

    factory = get_session_factory()
    if factory is None:
        return

    # 先清空内存中的 agent
    agent_manager.clear()

    async with factory() as session:
        result = await session.execute(
            select(AgentConfig).where(AgentConfig.is_active == True)
        )
        agents = result.scalars().all()

        for agent_row in agents:
            # 获取关联的工具
            result = await session.execute(
                select(ToolConfig, AgentToolConfig.sort_order)
                .join(AgentToolConfig, AgentToolConfig.tool_id == ToolConfig.id)
                .where(
                    AgentToolConfig.agent_id == agent_row.id,
                    ToolConfig.is_active == True
                )
                .order_by(AgentToolConfig.sort_order)
            )
            tool_rows = result.all()

            # 构建 ToolRegistration 列表
            tool_regs = []
            for tool_row, sort_order in tool_rows:
                reg = ToolRegistry.get(tool_row.name)
                if reg:
                    tool_regs.append(reg)
                else:
                    logger.warning(f"工具 '{tool_row.name}' 在DB中但未在registry中注册，跳过")

            try:
                # 动态实例化 Agent 类
                if agent_row.agent_class:
                    parts = agent_row.agent_class.rsplit(".", 1)
                    if len(parts) == 2:
                        module_path, class_name = parts
                        mod = __import__(module_path, fromlist=[class_name])
                        agent_cls = getattr(mod, class_name)
                    else:
                        agent_cls = None
                else:
                    agent_cls = None

                if agent_cls and hasattr(agent_cls, "load_from_db"):
                    # 使用类的 load_from_db 方法
                    agent = await agent_cls.load_from_db(agent_row, tool_regs)
                else:
                    # 通用方式：直接用 BaseAgent 创建
                    config = json.loads(agent_row.config_json or "{}")
                    cache_ttl = config.pop("cache_ttl", 900)
                    from agents.base import BaseAgent
                    agent = BaseAgent(
                        name=agent_row.name,
                        description=agent_row.description,
                        system_prompt=agent_row.system_prompt,
                        cache_ttl=cache_ttl,
                        **config
                    )
                    for reg in tool_regs:
                        agent.register_tool(Tool(
                            name=reg.name,
                            description=reg.description,
                            parameters=reg.parameters,
                            handler=reg.execute,
                        ))

                agent_manager.register(agent)
                logger.info(
                    f"[AgentLoad] 加载 Agent '{agent_row.name}' "
                    f"({len(tool_regs)} 个工具)"
                )
            except Exception as e:
                logger.error(f"[AgentLoad] 加载 Agent '{agent_row.name}' 失败: {e}")
