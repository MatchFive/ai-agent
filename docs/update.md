# 更新日志

## 2026-03-26

### 重要更新：API替换为国内可用的数据源 + 接口测试

**更新原因：**
原使用的国外API存在区域限制，国内访问不稳定。已全面替换为国内免费可用的数据源，并清理了所有国外API相关代码。

**变更内容：**

1. **黄金价格工具** (`tools/gold_price_tool.py`)
   - ❌ 删除：Metals-API (国外)
   - ✅ 新增：新浪财经/东方财富网 (国内)
   - ✅ 支持实时金价查询，无需API Key
   - ✅ 清理所有国外API相关代码和配置
   - ✅ 内置简化版HttpTool，无需外部依赖

2. **股票数据工具** (`tools/stock_data_tool.py`)
   - ❌ 删除：Alpha Vantage, yfinance (国外)
   - ✅ 新增：新浪财经/东方财富网 (国内)
   - ✅ 支持A股、港股、美股实时行情查询
   - ✅ 股票代码格式：
     - A股: `sh600519` (贵州茅台), `sz000001` (平安银行)
     - 港股: `hk00700` (腾讯控股)
     - 美股: `AAPL`, `TSLA`, `GOOGL`
   - ✅ 清理所有国外API相关代码和配置
   - ✅ 内置简化版HttpTool，无需外部依赖

3. **新闻工具** (`tools/news_tool.py`)
   - ❌ 删除：NewsAPI, GNews (国外)
   - ✅ 新增：新浪财经新闻/东方财富网新闻 (国内)
   - ✅ 支持中文关键词搜索
   - ✅ 模拟数据已改为中文
   - ✅ 清理所有国外API相关代码和配置
   - ✅ 内置简化版HttpTool，无需外部依赖

**配置文件更新：**
- `core/config.py` - 删除所有API Key配置项
  - 删除 `gold_api_key`, `gold_api_provider`
  - 删除 `stock_api_key`, `stock_api_provider`
  - 删除 `news_api_key`, `news_api_provider`

**代码优化：**
- 删除 `__init__` 中的 `api_key` 和 `api_provider` 参数
- 删除所有国外API的私有方法（`_fetch_from_metals_api`, `_fetch_from_alphavantage`, `_fetch_from_newsapi`）
- 简化主方法逻辑，直接调用国内API
- 重命名方法以更清晰（`_fetch_from_free_api` → `_fetch_from_sina`/`_fetch_from_eastmoney`）
- 内置简化版HttpTool类，避免依赖冲突

**接口测试结果：** (2026-03-26 15:20)
✅ **所有测试通过！**

| 工具 | 状态 | 数据源 | 测试结果 |
|------|------|--------|---------|
| 黄金价格 | ✅ PASS | 新浪财经 | 4472.81 USD (-2.46%) |
| A股数据 | ✅ PASS | 新浪财经 | 贵州茅台、平安银行 |
| 美股数据 | ✅ PASS | 新浪财经 | AAPL 252.62 (+0.98%) |
| 新闻资讯 | ✅ PASS | 新浪财经 | 3条财经新闻 |

详细测试报告见：`docs/api_test_report.md`

**优势：**
- ✅ 无需配置API Key即可使用（完全免费）
- ✅ 国内访问速度快，稳定可靠
- ✅ 支持中文关键词和A股市场数据
- ✅ 数据源互为备份，提高可用性
- ✅ 代码更简洁，无冗余逻辑
- ✅ 减少外部依赖

**使用说明：**
现在无需任何配置，直接实例化即可使用：
```python
# 获取黄金价格
gold_tool = GoldPriceTool()
price = await gold_tool.get_current_price()

# 查询A股
stock_tool = StockDataTool()
quote = await stock_tool.get_quote("sh600519")  # 贵州茅台

# 搜索中文新闻
news_tool = NewsTool()
news = await news_tool.search_financial_news("黄金 价格")
```

---

## 2026-03-25

### 新功能：投资理财分析 Agent

**功能描述：**
- 实现投资理财分析 Agent，支持黄金、股票走势分析
- 集成实时数据获取工具（黄金价格、股票数据、财经新闻）
- 前端对话界面，支持流式响应
- Agent 可调用工具获取实时数据

**新增文件：**

后端：
- `tools/gold_price_tool.py` - 黄金价格查询工具
- `tools/stock_data_tool.py` - 股票数据查询工具
- `tools/news_tool.py` - 财经新闻查询工具
- `agents/investment_agent.py` - 投资分析 Agent
- `api/schemas/agent.py` - Agent 相关 Schema
- `api/routers/agent.py` - Agent 对话路由

前端：
- `frontend/user/src/api/agent.js` - Agent API 封装
- `frontend/user/src/store/chat.js` - 对话状态管理
- `frontend/user/src/views/InvestmentChat.vue` - 对话界面

**修改文件：**
- `api/main.py` - 注册 agent_router
- `core/config.py` - 添加 API key 配置
- `tools/__init__.py` - 导出新工具
- `agents/__init__.py` - 导出 InvestmentAgent
- `frontend/user/src/router/index.js` - 添加投资分析路由
- `frontend/user/src/views/Home.vue` - 添加功能入口

**API 接口：**
- `GET /api/agent/info` - 获取 Agent 信息
- `POST /api/agent/chat` - 非流式对话
- `POST /api/agent/chat/stream` - 流式对话 (SSE)
- `POST /api/agent/reset` - 重置对话
- `GET /api/agent/tools` - 获取工具列表

**配置说明：**
需要在 `.env` 文件中配置以下 API Keys（可选，不配置则使用模拟数据）：
```
GOLD_API_KEY=your-key
STOCK_API_KEY=your-key
NEWS_API_KEY=your-key
```

---

### 功能更新：用户表添加 uid 字段

**变更内容：**
1. 用户表新增 `uid` 字段（UUID 类型），作为用户的唯一标识
2. `id` 保留为数据库主键，但不再用于业务逻辑
3. JWT token 的 `sub` 字段改为使用 `uid` 而非 `id`

**修改文件：**
- `api/models/user.py` - User 模型添加 uid 字段，自动生成 UUID
- `api/schemas/user.py` - UserResponse 添加 uid 字段
- `api/routers/auth.py` - create_access_token 使用 uid
- `api/deps.py` - 认证逻辑改为通过 uid 查询用户

**数据库迁移：**
- 后端启动时会自动为现有用户生成 uid
- 新用户创建时自动生成 uid

---

### Bug修复：管理端 API 401 未授权错误

**问题描述：**
- 管理端 Dashboard 页面调用 `/api/admin/stats` 返回 401 未授权

**根本原因：**
PyJWT 2.x 要求 JWT payload 中的 `sub` (subject) 字段必须是字符串类型，但代码中使用的是整数类型的 `user.id`，导致解码时报错 `InvalidSubjectError: Subject must be a string`

**解决方案：**
1. 修改 `api/routers/auth.py` 中的 `create_access_token` 函数，将 `user.id` 转为字符串：`str(user.id)`
2. 修改 `api/deps.py` 中的认证逻辑，在 JWT 解码后显式将 `user_id` 转换为整数类型

**修改文件：**
- `api/routers/auth.py`
- `api/deps.py`

---

## 2026-03-24

### Bug修复：favicon.ico 404 错误

**问题描述：**
- 访问管理端页面时，浏览器请求 `/favicon.ico` 返回 404 错误
- 原因：前端项目缺少 `public/` 目录和 `favicon.ico` 文件，且 `index.html` 未引用 favicon

**解决方案：**
1. 创建 `frontend/admin/public/` 和 `frontend/user/public/` 目录
2. 在两个前端项目的 `index.html` 中添加 favicon 引用：
   ```html
   <link rel="icon" type="image/x-icon" href="/favicon.ico">
   ```

**待完成：**
- 需要在 `frontend/admin/public/` 和 `frontend/user/public/` 目录中放置实际的 `favicon.ico` 文件
- 重新构建前端项目：`cd frontend/admin && npm run build`
- 部署更新后的 dist 目录到服务器
