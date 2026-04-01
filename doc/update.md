 # 更新日志

## 2026-04-01: 经验知识库功能

### 实现方案
新增全局共享的经验知识库：用户在对话中得到满意的解答后，手动触发将"问题+解决方案"保存为经验（存入 Milvus 向量数据库），后续任何人问类似问题时都能检索到相关经验辅助回答。经验库全局共享，每个 Agent 可通过 `config_json` 中的 `experience_kb.enabled` 独立控制是否启用检索。复用现有 KnowledgeBase 体系，新建 `经验库` KnowledgeBase 记录对应 Milvus collection `agent_experiences`。

### 变更内容

#### 修改文件
- `api/models/conversation.py` — 新增 AgentExperience 表（user_id、agent_name、question、answer、milvus_id、hit_count、last_referenced_at、created_at）
- `api/schemas/agent.py` — 新增 SaveExperienceRequest schema
- `api/routers/agent.py` — 新增 `_is_experience_kb_enabled`、`_inject_experiences`、`_record_experience_hits` 辅助函数；chat/chat_stream 中注入经验检索；新增保存经验 API（用户侧不暴露列表/删除接口）
- `core/startup.py` — 新增 `init_experience_kb()`（创建 Milvus collection + seed 经验库 KB 记录）、`cleanup_stale_experiences()`（闲置清理）；InvestmentAgent 和 UnityAgent 种子数据加入 `"experience_kb": {"enabled": true}`
- `api/main.py` — lifespan 中调用 `init_experience_kb()` 和 `cleanup_stale_experiences()`
- `frontend/user/src/components/ChatPanel.vue` — 助手消息 hover 显示"存为经验"按钮
- `frontend/user/src/api/agent.js` — 新增 `saveExperience` API 方法

#### 新增数据库表
- `agent_experiences` — 经验元数据（user_id、agent_name、question、answer、milvus_id、hit_count、last_referenced_at、created_at）

#### 新增 API 接口
- `POST /api/agent/experiences` — 保存经验（传入 conversation_id + question_index，从对话中提取 Q&A 对）

#### 闲置清理机制
- 服务启动时执行 `cleanup_stale_experiences()`
- 清理规则：创建超过 30 天且从未被检索命中，或超过 60 天未被命中的经验
- 同时清理 Milvus 和 MySQL 记录
- 每次经验被检索命中时，异步更新 `hit_count` 和 `last_referenced_at`

#### 新增 KnowledgeBase 种子数据
- `经验库` — collection_name=`agent_experiences`，embedding_dim=1024

#### 经验检索链路
- 用户提问 → 检查 Agent `experience_kb.enabled` → embed query → VectorStore.search(collection="agent_experiences", top_k=3) → 格式化为 `[相关经验]` 系统消息 → 注入 Agent 短期记忆 → 异步更新命中记录 → LLM 回答

## 2026-04-01: Agent 长期记忆功能

### 实现方案
新增跨对话的长期记忆系统：每次助手回复后异步调用 LLM 提取有价值信息存入 Milvus 向量数据库，下次对话前检索相关记忆注入上下文。使用单一 Milvus collection + user_id 过滤实现用户隔离，通过 Agent config_json 中的 `long_term_memory.enabled` 按 Agent 独立控制开关。

### 变更内容

#### 新增文件
- `core/long_term_memory.py` — LongTermMemoryManager 核心类（retrieve、extract_and_store、format_memories_as_context、ensure_collection、delete_memory/delete_memories）

#### 修改文件
- `core/vectorstore.py` — 新增 create_collection（幂等）、insert（批量插入）、search 扩展（filter_expr/output_fields 参数）、delete_by_ids 方法；新增长期记忆 collection schema 定义
- `core/config.py` — 新增 ltm_enabled、ltm_max_memories、ltm_extraction_max_tokens、ltm_collection_name 配置项
- `api/models/conversation.py` — 新增 UserLongTermMemory 表（user_id、milvus_id、text、category、importance、agent_name、conversation_id、created_at）
- `api/routers/agent.py` — 非流式/流式 chat 接口集成长期记忆检索+提取；新增 _is_ltm_enabled、_inject_long_term_memories 辅助函数；新增 3 个记忆管理 API
- `api/schemas/agent.py` — 新增 MemoryItemSchema、MemoryListResponse schema
- `core/startup.py` — 新增 init_long_term_memory() 函数；InvestmentAgent 种子数据启用长期记忆；UnityAgent 种子数据禁用长期记忆
- `api/main.py` — lifespan 中调用 init_long_term_memory()
- `develop.md` — 更新项目结构

#### 新增数据库表
- `user_long_term_memories` — 用户长期记忆元数据（用于分页查询和删除定位）

#### 新增 API 接口
- `GET /api/agent/memories` — 分页查询当前用户长期记忆（支持 category 过滤）
- `DELETE /api/agent/memories/{id}` — 删除单条长期记忆（同时删 Milvus + MySQL）
- `DELETE /api/agent/memories` — 清空当前用户所有长期记忆

#### Milvus Collection
- `agent_long_term_memory` — 单一 collection，schema 包含 id(PK/auto_id)、embedding(FLOAT_VECTOR)、text、user_id、agent_name、category、importance、created_at、conversation_id

#### 长期记忆链路
- **检索链路**: 用户提问 → embed query → VectorStore.search(filter=user_id) → 格式化为系统消息 → 注入 Agent 短期记忆 → LLM 回答
- **提取链路**: 助手回复完成 → asyncio.create_task(fire-and-forget) → LLM 分析对话轮次 → 提取记忆列表 → embed → insert Milvus + MySQL
- **记忆分类**: preference(偏好)、fact(事实)、context(上下文)、instruction(指令)
- **重要程度**: 1-5 分，用于未来去重/衰减策略

#### Agent 级别开关
- InvestmentAgent: `"long_term_memory": {"enabled": true}`
- UnityAgent: `"long_term_memory": {"enabled": false}`（RAG Agent 暂不开长期记忆）

## 2026-04-01: 对话历史回顾 + 新建对话

### 实现方案
在现有 conversations 表基础上新增 agent_name 和 title 字段，新增对话历史列表/详情/删除/更新标题 4 个 API 接口，前端改造为三栏布局（Agent 图标栏 + 对话列表 + 聊天面板），支持查看历史对话和手动新建对话。

### 变更内容

#### 修改文件
- `api/models/conversation.py` — Conversation 表新增 agent_name、title 字段；DatabaseStorage 支持写入 agent_name
- `api/models/user.py` — init_db 增加 ALTER TABLE 迁移逻辑（兼容已有表）
- `api/schemas/agent.py` — 新增 ConversationListItem、ConversationDetail、ConversationListResponse、UpdateTitleRequest schemas
- `api/routers/agent.py` — 新增 4 个对话历史接口；_setup_conversation 传入 agent_name
- `frontend/user/src/api/agent.js` — 新增 getConversations、getConversation、updateConversationTitle、deleteConversation
- `frontend/user/src/store/chat.js` — 新增对话列表状态和 actions（fetchConversations、loadConversation、newConversation、deleteConversation、updateTitle）
- `frontend/user/src/components/AgentSidebar.vue` — 缩窄为 60px 图标模式
- `frontend/user/src/components/ChatPanel.vue` — 支持加载历史对话、自动标题、发送后刷新列表

#### 新增文件
- `frontend/user/src/components/ConversationList.vue` — 对话历史列表面板

#### 修改布局
- `frontend/user/src/views/Home.vue` — 三栏布局：AgentSidebar(60px) | ConversationList(220px) | ChatPanel(flex)

#### 新增 API 接口
- `GET /api/agent/conversations?agent_name=xxx` — 获取对话历史列表（分页）
- `GET /api/agent/conversations/{id}` — 获取对话详情（含完整消息）
- `DELETE /api/agent/conversations/{id}` — 删除对话
- `PUT /api/agent/conversations/{id}/title` — 更新对话标题

#### 前端交互流程
1. 选择 Agent → 加载该 Agent 的对话历史列表
2. 点击历史对话 → 加载消息内容
3. 点击"新建对话" → 清空状态开始新对话
4. 发送首条消息后自动以消息前 20 字作为标题
5. 切换对话时通过 key 变化重建 ChatPanel 组件

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
