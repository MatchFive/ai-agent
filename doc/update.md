# 更新日志

## 2026-03-30: Agent/Tool 动态配置化

### 实现方案
将 Agent 的系统提示词和可用工具从硬编码改为数据库配置，通过装饰器自动发现工具。

### 变更内容

#### 新增文件
- `tools/registry.py` — 工具注册表（ToolRegistration、ToolRegistry、@register_tool、@register_method_tool 装饰器、scan_classes_for_method_tools）
- `api/models/agent_config.py` — 3 张新表：agent_configs、tool_configs、agent_tool_configs
- `api/schemas/admin_tools.py` — Admin 管理接口 Pydantic schemas
- `api/routers/admin_tools.py` — Admin 管理 Agent 和 Tool 的路由（CRUD + 关联管理 + 热加载）
- `core/startup.py` — 启动模块（import_tools、sync_tools_to_db、seed_default_agents、load_agents_from_db）

#### 修改文件
- `tools/gold_price_tool.py` — 加 @register_tool 装饰器
- `tools/stock_data_tool.py` — 加 @register_method_tool 装饰器（get_stock_quote、get_multiple_stock_quotes）
- `tools/news_tool.py` — 加 @register_method_tool 装饰器（search_news、search_news_by_topic）
- `tools/email_tool.py` — 加 @register_method_tool 装饰器（send_email、send_text_email）
- `tools/file_tool.py` — 加 @register_method_tool 装饰器（7 个方法）
- `tools/http_tool.py` — 加 @register_method_tool 装饰器（5 个方法）
- `tools/scheduler_tool.py` — 加 @register_method_tool 装饰器（4 个方法）
- `tools/__init__.py` — 导出 registry 模块
- `agents/base.py` — 添加 cache_ttl 参数、Redis 缓存逻辑（从 InvestmentAgent 移入）、load_from_db 类方法
- `agents/investment_agent.py` — 删除 execute_tool 覆写（缓存已在 BaseAgent 中）
- `api/routers/agent.py` — 改为从 agent_manager 获取 Agent，新增 /list 接口
- `api/routers/__init__.py` — 导出 admin_tools_router
- `api/main.py` — lifespan 中加入启动流程（工具扫描→DB同步→种子数据→Agent加载）
- `develop.md` — 更新项目结构

#### 新增数据库表
- `agent_configs` — Agent 配置（name、system_prompt、agent_class、config_json、is_active）
- `tool_configs` — 工具配置（name、description、parameters_json、handler_class、handler_method、category、version_hash）
- `agent_tool_configs` — Agent-工具关联（agent_id、tool_id、sort_order）

#### 新增 API 接口
- `GET /api/admin/tools` — 列出所有工具
- `POST /api/admin/tools/reload` — 重新扫描并同步工具（热加载）
- `GET /api/admin/tools/{tool_id}` — 工具详情
- `PUT /api/admin/tools/{tool_id}` — 更新工具
- `PATCH /api/admin/tools/{tool_id}` — 启用/禁用工具
- `GET /api/admin/agents` — 列出所有 Agent
- `POST /api/admin/agents` — 创建 Agent
- `GET /api/admin/agents/{agent_id}` — Agent 详情
- `PUT /api/admin/agents/{agent_id}` — 更新 Agent
- `PATCH /api/admin/agents/{agent_id}` — 启用/禁用 Agent
- `DELETE /api/admin/agents/{agent_id}` — 删除 Agent
- `POST /api/admin/agents/{agent_id}/tools` — 设置工具关联
- `DELETE /api/admin/agents/{agent_id}/tools/{tool_id}` — 移除工具关联
- `GET /api/agent/list` — 获取所有可用 Agent

### 共注册 23 个工具
- finance: get_gold_price、get_stock_quote、get_multiple_stock_quotes、search_news、search_news_by_topic
- communication: send_email、send_text_email
- file: file_read、file_write、file_read_json、file_write_json、file_delete、file_list_directory、file_create_directory
- http: http_get、http_post、http_put、http_delete、http_download
- scheduler: scheduler_add_cron、scheduler_add_interval、scheduler_remove_job、scheduler_list_jobs
