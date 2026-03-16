# AI-Agent 多Agent集成框架

一个灵活的多Agent集成系统，支持多种不同功能的Agent，共享公共工具模块，并提供完整的前后端账户管理系统。

## 特性

- **多Agent架构**: 支持多种类型Agent，各司其职
- **工具复用**: 公共工具模块可在不同Agent间共享
- **账户系统**: 完整的用户注册、登录、权限管理
- **邀请码机制**: 管理员生成邀请码，用户注册时验证
- **前后端分离**: FastAPI后端 + Vue3前端
- **异步支持**: 全面支持异步操作
- **MySQL数据库**: 使用pymysql连接池

## 项目结构

```
ai-agent/
├── agents/                 # Agent模块
│   ├── base.py            # Agent基类
│   └── manager.py         # Agent管理器
├── tools/                  # 公共工具模块
│   ├── email_tool.py      # 邮件发送
│   ├── scheduler_tool.py  # 定时任务
│   ├── file_tool.py       # 文件操作
│   ├── http_tool.py       # HTTP请求
│   └── database_tool.py   # 数据库操作
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── llm.py             # LLM接口封装
│   ├── memory.py          # 记忆/上下文管理
│   └── logger.py          # 日志系统
├── api/                    # 后端API
│   ├── main.py            # FastAPI主入口
│   ├── deps.py            # 依赖注入
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic模型
│   └── routers/           # 路由
│       ├── auth.py        # 认证路由
│       └── admin.py       # 管理员路由
├── frontend/               # 前端项目
│   ├── user/              # 用户端Vue项目
│   └── admin/             # 管理端Vue项目
├── config/                 # 配置文件
│   └── settings.yaml      # 主配置
├── requirements.txt        # Python依赖
└── README.md              # 说明文档
```

## 快速开始

### 1. 创建MySQL数据库

```sql
CREATE DATABASE ai_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 安装后端依赖

```bash
cd ai-agent
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息
```

环境变量配置示例：
```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=ai_agent

# JWT密钥
SECRET_KEY=your-secret-key-change-in-production
```

### 4. 启动后端服务

```bash
# 开发模式
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 或者
cd api && python main.py
```

### 5. 安装前端依赖

```bash
# 用户端
cd frontend/user
npm install

# 管理端
cd frontend/admin
npm install
```

### 6. 启动前端服务

```bash
# 用户端 (http://localhost:3000)
cd frontend/user
npm run dev

# 管理端 (http://localhost:3001)
cd frontend/admin
npm run dev
```

## 账户系统

### 默认管理员账号

- 用户名: `admin`
- 密码: `123456`

### 用户注册流程

1. 管理员在管理后台生成邀请码
2. 用户在注册页面填写用户名、密码和邀请码
3. 邀请码验证通过后，用户注册成功
4. 邀请码自动标记为已使用

### 功能权限

| 功能 | 用户 | 管理员 |
|------|------|--------|
| 登录 | ✅ | ✅ |
| 注册(需邀请码) | ✅ | - |
| 生成邀请码 | - | ✅ |
| 删除邀请码 | - | ✅ |
| 查看用户列表 | - | ✅ |
| 启用/禁用用户 | - | ✅ |

## API接口

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 登录 |
| `/api/auth/register` | POST | 注册 |
| `/api/auth/me` | GET | 获取当前用户 |

### 管理员接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/admin/stats` | GET | 获取统计数据 |
| `/api/admin/invite-codes` | GET | 获取邀请码列表 |
| `/api/admin/invite-codes` | POST | 生成邀请码 |
| `/api/admin/invite-codes/{id}` | DELETE | 删除邀请码 |
| `/api/admin/users` | GET | 获取用户列表 |
| `/api/admin/users/{id}/toggle-active` | POST | 启用/禁用用户 |

## 数据库

使用MySQL数据库，通过pymysql连接。

### 连接配置

```yaml
# config/settings.yaml
database:
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: ai_agent
  charset: utf8mb4
```

### 表结构

**用户表 (users)**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(50) | 用户名 |
| password_hash | String(255) | 密码哈希 |
| role | String(20) | 角色(admin/user) |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |

**邀请码表 (invite_codes)**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String(32) | 邀请码 |
| is_used | Boolean | 是否已使用 |
| created_by | Integer | 创建者ID |
| used_by | Integer | 使用者ID |
| created_at | DateTime | 创建时间 |
| used_at | DateTime | 使用时间 |

### 连接池配置

```python
# api/models/user.py
engine = create_async_engine(
    db_url,
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    pool_timeout=30,        # 获取连接超时时间
    pool_recycle=3600,      # 连接回收时间(1小时)
    pool_pre_ping=True,     # 连接前检查可用性
)
```

## 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM
- pymysql - MySQL连接库
- aiomysql - 异步MySQL驱动
- PyJWT - JWT认证
- Passlib - 密码加密
- Pydantic - 数据验证

### 前端
- Vue 3 - 前端框架
- Vue Router - 路由
- Pinia - 状态管理
- Element Plus - UI组件库
- Axios - HTTP客户端
- Vite - 构建工具

## 许可证

MIT License
