# 更新日志

## 2026-03-30: RAG 知识库通用化改造

### 实现方案
将 RAG 知识库从全局单一 collection 改为数据库多知识库管理，新增 knowledge_bases 表和 Admin CRUD 接口，rag_search 工具按知识库名称检索对应 Milvus collection。

### 变更内容

#### 修改文件
- `api/models/agent_config.py` — 新增 KnowledgeBase 表（name、description、collection_name、embedding_dim、is_active）
- `tools/rag_tool.py` — 参数新增 knowledge_base（必需），运行时查 DB 获取 collection_name
- `core/vectorstore.py` — search() 的 collection_name 改为必传参数，不再从 settings 读默认值
- `core/config.py` — 删除 milvus_collection 配置项（collection 现在按知识库维度管理）
- `api/schemas/admin_tools.py` — 新增 KnowledgeBaseCreate/Update/Response schemas
- `api/routers/admin_tools.py` — 新增知识库 CRUD 接口（6 个）
- `core/startup.py` — 新增 seed 默认知识库记录（Unity手册），UnityAgent config_json 加入 knowledge_base
- `agents/unity_agent.py` — 新增 knowledge_base 属性，run/run_stream 传 knowledge_base 参数

#### 新增数据库表
- `knowledge_bases` — 知识库配置（name、description、collection_name、embedding_dim、is_active）

#### 新增 API 接口
- `GET /api/admin/knowledge-bases` — 列出所有知识库
- `POST /api/admin/knowledge-bases` — 创建知识库
- `GET /api/admin/knowledge-bases/{id}` — 知识库详情
- `PUT /api/admin/knowledge-bases/{id}` — 更新知识库
- `PATCH /api/admin/knowledge-bases/{id}` — 启用/禁用知识库
- `DELETE /api/admin/knowledge-bases/{id}` — 删除知识库

#### RAG 链路变更
- 旧流程：rag_search(query) → 从 settings 读 milvus_collection → 搜索
- 新流程：rag_search(knowledge_base, query) → 查 DB 获取 collection_name → 搜索

## 2026-03-31: Unity 入门小助手（RAG Agent）

### 实现方案
基于 Milvus 向量数据库 + Embedding 服务 + LLM 实现 RAG 知识问答链路，创建 Unity 入门小助手 Agent。

### 变更内容

#### 新增文件
- `core/embedding.py` — Embedding 客户端（OpenAI 兼容接口，支持批量调用）
- `core/vectorstore.py` — Milvus 向量存储客户端（连接、搜索）
- `tools/rag_tool.py` — RAG 知识库检索工具（@register_tool 装饰器，category="rag"）
- `agents/unity_agent.py` — Unity 入门小助手 Agent（继承 BaseAgent，实现 RAG 流程）

#### 修改文件
- `core/config.py` — 添加 Embedding 配置（base_url、model、batch_size）和 Milvus 配置（host、port、collection、dim）
- `core/startup.py` — import_tools 加入 rag_tool；seed_default_agents 加入 UnityAgent 种子数据
- `requirements.txt` — 添加 pymilvus>=2.3.0
- `develop.md` — 更新项目结构

#### RAG 链路流程
1. 用户提问 → RAGSearchTool.search()
2. query → EmbeddingClient.embed_single() → 向量
3. 向量 → VectorStore.search() → Milvus COSINE 搜索 top_k=5
4. 检索文档 + 用户问题 → 注入上下文 → LLM 生成回答

#### 新增工具
- rag_search (category="rag") — 参数: query(必需), top_k(默认5)

#### 新增 Agent
- UnityAgent — 系统提示词引导为 Unity 入门助手，每次请求先检索再回答，cache_ttl=0（RAG 不缓存）

#### 依赖
- pymilvus>=2.3.0
- Embedding 服务: Qwen3-Embedding-0.6B (OpenAI 兼容接口，本地 8000 端口)
- Milvus: localhost:19530，已有 collection unity_docs_2022_3

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
