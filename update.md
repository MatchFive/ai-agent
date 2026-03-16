# AI-Agent 多Agent集成项目实现计划

## 项目概述
构建一个多Agent集成系统，支持多种不同功能的Agent，共享公共工具模块，并提供完整的前后端账户管理系统。

---

## 一、账户系统设计

### 1.1 数据库表设计

#### 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String | 用户名 (唯一) |
| password_hash | String | 密码哈希 |
| role | String | 角色 (admin/user) |
| is_active | Boolean | 是否激活 |
| created_at | DateTime | 创建时间 |

#### 邀请码表 (invite_codes)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| code | String | 邀请码 (唯一) |
| is_used | Boolean | 是否已使用 |
| used_by | Integer | 使用者ID |
| created_at | DateTime | 创建时间 |
| used_at | DateTime | 使用时间 |

### 1.2 API设计

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 登录 |
| /api/auth/register | POST | 注册 |
| /api/auth/me | GET | 获取当前用户 |
| /api/admin/invite-codes | GET | 获取邀请码列表 |
| /api/admin/invite-codes | POST | 生成邀请码 |
| /api/admin/invite-codes/{id} | DELETE | 删除邀请码 |
| /api/admin/users | GET | 获取用户列表 |
| /api/admin/users/{id}/toggle-active | POST | 启用/禁用用户 |
| /api/admin/stats | GET | 获取统计数据 |

### 1.3 前端页面

#### 用户端 (端口3000)
- 登录页 `/login`
- 注册页 `/register` (需要邀请码)
- 主页 `/` (登录后)

#### 管理端 (端口3001)
- 登录页 `/login`
- 仪表盘 `/dashboard`
- 邀请码管理 `/invite-codes`
- 用户管理 `/users`

---

## 二、实现步骤

### Phase 1: 清理和准备
- [x] 删除具体Agent实现
- [x] 创建API目录结构

### Phase 2: 后端API
- [x] 创建数据模型 (User, InviteCode)
- [x] 创建Pydantic schemas
- [x] 实现认证路由 (登录/注册)
- [x] 实现管理员路由 (邀请码/用户管理)
- [x] 创建FastAPI主入口
- [x] JWT认证中间件
- [x] MySQL数据库支持 (pymysql)

### Phase 3: 前端 - 用户端
- [x] 创建Vue项目结构
- [x] 实现登录页
- [x] 实现注册页
- [x] 实现主页
- [x] 路由守卫

### Phase 4: 前端 - 管理端
- [x] 创建Vue项目结构
- [x] 实现登录页
- [x] 实现布局组件
- [x] 实现仪表盘
- [x] 实现邀请码管理
- [x] 实现用户管理

### Phase 5: 服务管理
- [x] 环境初始化脚本 init_env.sh
- [x] 启动脚本 start_server.sh
- [x] 停止脚本 stop_server.sh

---

## 三、实现记录

### 已实现文件清单

#### 后端 API
| 文件路径 | 说明 |
|----------|------|
| `api/__init__.py` | API模块初始化 |
| `api/main.py` | FastAPI主入口 |
| `api/deps.py` | 依赖注入(认证中间件) |
| `api/models/__init__.py` | 模型导出 |
| `api/models/user.py` | 用户和邀请码模型 (MySQL) |
| `api/schemas/__init__.py` | Schema导出 |
| `api/schemas/user.py` | Pydantic schemas |
| `api/routers/__init__.py` | 路由导出 |
| `api/routers/auth.py` | 认证路由 |
| `api/routers/admin.py` | 管理员路由 |

#### 前端 - 用户端
| 文件路径 | 说明 |
|----------|------|
| `frontend/user/package.json` | 项目配置 |
| `frontend/user/vite.config.js` | Vite配置 |
| `frontend/user/index.html` | HTML入口 |
| `frontend/user/src/main.js` | Vue入口 |
| `frontend/user/src/App.vue` | 根组件 |
| `frontend/user/src/router/index.js` | 路由配置 |
| `frontend/user/src/store/user.js` | 用户状态管理 |
| `frontend/user/src/api/auth.js` | API封装 |
| `frontend/user/src/views/Login.vue` | 登录页 |
| `frontend/user/src/views/Register.vue` | 注册页 |
| `frontend/user/src/views/Home.vue` | 主页 |

#### 前端 - 管理端
| 文件路径 | 说明 |
|----------|------|
| `frontend/admin/package.json` | 项目配置 |
| `frontend/admin/vite.config.js` | Vite配置 |
| `frontend/admin/index.html` | HTML入口 |
| `frontend/admin/src/main.js` | Vue入口 |
| `frontend/admin/src/App.vue` | 根组件 |
| `frontend/admin/src/router/index.js` | 路由配置 |
| `frontend/admin/src/store/admin.js` | 管理员状态管理 |
| `frontend/admin/src/api/auth.js` | API封装 |
| `frontend/admin/src/views/Login.vue` | 登录页 |
| `frontend/admin/src/views/Layout.vue` | 布局组件 |
| `frontend/admin/src/views/Dashboard.vue` | 仪表盘 |
| `frontend/admin/src/views/InviteCodes.vue` | 邀请码管理 |
| `frontend/admin/src/views/Users.vue` | 用户管理 |

#### 服务脚本
| 文件路径 | 说明 |
|----------|------|
| `init_env.sh` | 环境初始化脚本 |
| `start_server.sh` | 服务启动脚本 |
| `stop_server.sh` | 服务停止脚本 |

---

## 四、使用说明

### 快速开始

```bash
# 1. 添加执行权限
chmod +x init_env.sh start_server.sh stop_server.sh

# 2. 检查环境依赖
./init_env.sh check

# 3. 初始化所有环境
./init_env.sh all

# 4. 编辑配置文件
vim .env

# 5. 启动服务
./start_server.sh
```

### 环境初始化脚本

```bash
# 初始化所有环境
./init_env.sh all

# 初始化指定环境
./init_env.sh backend   # 后端Python环境
./init_env.sh frontend  # 前端环境
./init_env.sh user      # 仅用户端前端
./init_env.sh admin     # 仅管理端前端
./init_env.sh db        # MySQL数据库

# 检查环境依赖
./init_env.sh check
```

### 服务管理脚本

```bash
# 启动服务
./start_server.sh          # 启动所有服务
./start_server.sh backend  # 仅后端
./start_server.sh user     # 仅用户端
./start_server.sh admin    # 仅管理端

# 停止服务
./stop_server.sh           # 停止所有服务
./stop_server.sh backend
./stop_server.sh user
./stop_server.sh admin

# 查看服务状态
./stop_server.sh status
```

### 服务地址

| 服务 | 地址 |
|------|------|
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |
| 用户端 | http://localhost:3000 |
| 管理端 | http://localhost:3001 |

### 默认管理员
- 用户名: `admin`
- 密码: `123456`

---

## 五、数据库配置

### MySQL配置
```yaml
database:
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: ai_agent
  charset: utf8mb4
```

### 创建数据库
```sql
CREATE DATABASE ai_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

*计划创建时间: 2026-03-16*
*实现完成时间: 2026-03-16*
