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
- **一键部署**: 环境初始化和服务管理脚本

## 项目结构

```
ai-agent/
├── agents/                 # Agent模块
│   ├── base.py            # Agent基类
│   └── manager.py         # Agent管理器
├── tools/                  # 公共工具模块
│   ├── database_tool.py   # 数据库工具
│   ├── email_tool.py      # 邮件工具
│   ├── file_tool.py       # 文件工具
│   ├── http_tool.py       # HTTP请求工具
│   └── scheduler_tool.py  # 调度工具
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── llm.py             # LLM接口
│   ├── logger.py          # 日志模块
│   └── memory.py          # 记忆模块
├── api/                    # 后端API
│   ├── models/            # 数据模型
│   ├── routers/           # 路由模块
│   │   ├── admin.py      # 管理员路由
│   │   └── auth.py       # 认证路由
│   └── schemas/           # 数据模式
├── frontend/               # 前端项目
│   ├── user/              # 用户端Vue项目
│   └── admin/             # 管理端Vue项目
├── command/                # 命令脚本
│   ├── init_env.sh        # 环境初始化脚本
│   ├── init_database.sh   # 数据库初始化脚本
│   ├── init_database.sql  # 数据库初始化SQL
│   └── quick_setup.sh     # 快速安装脚本
├── deploy/                 # 部署相关
│   ├── deploy.sh          # 部署脚本
│   ├── check.sh           # 检查脚本
│   └── nginx/             # Nginx配置
├── config/                 # 配置文件
│   └── settings.yaml      # 应用配置
├── tests/                  # 测试文件
├── scripts/                # 工具脚本
├── logs/                   # 日志目录
├── data/                   # 数据目录
├── build.sh               # 构建脚本
├── start_server.sh        # 服务启动脚本
├── stop_server.sh         # 服务停止脚本
├── requirements.txt        # Python依赖
└── README.md              # 说明文档
```

## 快速开始

### 方式一：快速安装（推荐）

```bash
# 使用快速安装脚本（自动完成所有初始化）
./command/quick_setup.sh
```

### 方式二：一键初始化

```bash
# 1. 添加执行权限
chmod +x command/*.sh start_server.sh stop_server.sh build.sh

# 2. 检查环境依赖
./command/init_env.sh check

# 3. 初始化所有环境（后端+前端+数据库）
./command/init_env.sh all

# 4. 编辑配置文件
vim .env  # 配置数据库密码等

# 5. 启动服务
./start_server.sh
```

### 方式三：分步初始化

```bash
# 初始化后端环境
./command/init_env.sh backend

# 初始化前端环境
./command/init_env.sh frontend

# 初始化数据库
./command/init_env.sh db
```

### 方式三：手动初始化

#### 1. 创建MySQL数据库

```sql
CREATE DATABASE ai_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

#### 4. 安装前端依赖

```bash
cd frontend/user && npm install
cd frontend/admin && npm install
```

## 服务管理

### 启动服务

```bash
# 启动所有服务
./start_server.sh

# 启动指定服务
./start_server.sh backend   # 仅后端
./start_server.sh user      # 仅用户端
./start_server.sh admin     # 仅管理端
```

### 停止服务

```bash
# 停止所有服务
./stop_server.sh

# 停止指定服务
./stop_server.sh backend
./stop_server.sh user
./stop_server.sh admin

# 查看服务状态
./stop_server.sh status
```

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端API | http://localhost:8000 | FastAPI服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| 用户端 | http://localhost:3000 | Vue3前端 |
| 管理端 | http://localhost:3001 | Vue3前端 |

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

## 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | >= 3.9 | 后端运行环境 |
| Node.js | >= 16.0 | 前端构建工具 |
| npm | >= 8.0 | 前端包管理 |
| MySQL | >= 5.7 | 数据库 |

## 配置说明

### 环境变量 (.env)

```env
# 应用配置
SECRET_KEY=your-secret-key-change-in-production

# MySQL数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_DATABASE=ai_agent

# LLM配置（可选）
ANTHROPIC_API_KEY=your_api_key_here
```

### 应用配置 (config/settings.yaml)

项目使用YAML格式的配置文件，支持更灵活的配置管理。

## 部署

项目提供了完整的部署方案，详见 `deploy/` 目录：

- **deploy/deploy.sh** - 自动化部署脚本
- **deploy/check.sh** - 环境检查脚本
- **deploy/nginx/** - Nginx配置示例
- **deploy/DEPLOYMENT.md** - 详细部署文档

### 快速部署

```bash
# 检查部署环境
./deploy/check.sh

# 执行部署
./deploy/deploy.sh
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/
```

### 构建项目

```bash
# 使用构建脚本
./build.sh
```

## 技术栈

### 后端
- FastAPI - Web框架
- SQLAlchemy - ORM
- pymysql - MySQL连接库
- aiomysql - 异步MySQL驱动
- PyJWT - JWT认证
- Passlib - 密码加密

### 前端
- Vue 3 - 前端框架
- Vue Router - 路由
- Pinia - 状态管理
- Element Plus - UI组件库
- Vite - 构建工具

## 许可证

MIT License
