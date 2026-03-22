# 数据库权限问题解决方案

## 问题描述

启动后端服务时遇到以下错误：

```
pymysql.err.OperationalError: (1142, "SELECT command denied to user 'ai_agent'@'localhost' for table 'users'")
```

## 问题原因

这是**数据库用户权限不足**的问题，不是数据库未初始化。

错误含义：
- ✅ 数据库连接成功
- ✅ 数据库 `ai_agent` 存在
- ❌ 用户 `ai_agent` 没有足够的权限操作表

## 解决方案

### 方案 1：使用自动脚本（推荐）

```bash
# 运行数据库初始化脚本
chmod +x init_database.sh
bash init_database.sh
```

脚本会自动：
1. 测试 MySQL root 连接
2. 创建数据库（如果不存在）
3. 创建用户并授权
4. 测试用户连接

### 方案 2：手动执行 SQL

#### 步骤 1：修改 SQL 文件

编辑 `init_database.sql`，将 `'your_password_here'` 替换为你的实际密码：

```sql
CREATE USER IF NOT EXISTS 'ai_agent'@'localhost' IDENTIFIED BY 'your_password_here';
```

#### 步骤 2：执行 SQL

```bash
mysql -u root -p < init_database.sql
```

### 方案 3：手动在 MySQL 中执行

```bash
# 登录 MySQL
mysql -u root -p
```

然后执行：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS `ai_agent`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 创建用户（替换密码）
CREATE USER IF NOT EXISTS 'ai_agent'@'localhost' IDENTIFIED BY '你的密码';

-- 授予权限（推荐）
GRANT ALL PRIVILEGES ON `ai_agent`.* TO 'ai_agent'@'localhost';

-- 或者授予最小权限（更安全）
-- GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER
-- ON `ai_agent`.* TO 'ai_agent'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证
SHOW GRANTS FOR 'ai_agent'@'localhost';

-- 退出
EXIT;
```

## 权限说明

### 完整权限（推荐用于开发环境）

```sql
GRANT ALL PRIVILEGES ON `ai_agent`.* TO 'ai_agent'@'localhost';
```

包含：
- SELECT, INSERT, UPDATE, DELETE - 数据操作
- CREATE, DROP, ALTER, INDEX - 表结构操作
- REFERENCES, CREATE TEMPORARY TABLES - 其他功能

### 最小权限（推荐用于生产环境）

```sql
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER
ON `ai_agent`.* TO 'ai_agent'@'localhost';
```

## 验证权限

```bash
# 登录 MySQL
mysql -u root -p

# 查看用户权限
SHOW GRANTS FOR 'ai_agent'@'localhost';

# 测试用户连接
mysql -u ai_agent -p -e "USE ai_agent; SHOW TABLES;"
```

## 常见问题

### Q1: 用户已存在但权限不足

**解决**：

```sql
-- 重新授权
GRANT ALL PRIVILEGES ON `ai_agent`.* TO 'ai_agent'@'localhost';
FLUSH PRIVILEGES;
```

### Q2: 忘记 ai_agent 用户密码

**解决**：

```sql
-- 重置密码
ALTER USER 'ai_agent'@'localhost' IDENTIFIED BY '新密码';
FLUSH PRIVILEGES;
```

### Q3: 需要从任何主机连接

**解决**：

```sql
-- 授权从任何主机连接
GRANT ALL PRIVILEGES ON `ai_agent`.* TO 'ai_agent'@'%';
FLUSH PRIVILEGES;
```

**注意**: 生产环境不推荐，有安全风险。

### Q4: 需要删除用户重新创建

**解决**：

```sql
-- 删除用户
DROP USER 'ai_agent'@'localhost';

-- 重新创建
CREATE USER 'ai_agent'@'localhost' IDENTIFIED BY '密码';
GRANT ALL PRIVILEGES ON `ai_agent`.* TO 'ai_agent'@'localhost';
FLUSH PRIVILEGES;
```

## 配置 .env 文件

确保 `.env` 文件中的数据库配置正确：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=ai_agent
DB_PASSWORD=你的密码
DB_DATABASE=ai_agent
```

## 重启服务

解决权限问题后，重启后端服务：

```bash
# 停止服务
./stop_server.sh backend

# 启动服务
./start_server.sh backend

# 查看日志
tail -f logs/backend.log
```

## 检查数据库表

服务启动成功后，检查表是否自动创建：

```bash
# 登录数据库
mysql -u ai_agent -p

# 使用数据库
USE ai_agent;

# 查看表
SHOW TABLES;

# 查看用户表结构
DESCRIBE users;

# 查看默认管理员
SELECT id, username, role, is_active, created_at FROM users;
```

应该看到：
- `users` 表
- `invite_codes` 表
- 默认管理员账号：`admin` / `123456`

## 安全建议

### 开发环境
- 使用 `ALL PRIVILEGES`
- 密码可以简单一些

### 生产环境
- 使用最小权限原则
- 使用强密码
- 限制访问主机（不用 `%`）
- 定期更换密码
- 启用 SSL 连接

## 完整流程

```bash
# 1. 初始化数据库
bash init_database.sh

# 2. 检查配置
cat .env | grep DB_

# 3. 测试数据库连接
mysql -u ai_agent -p -e "USE ai_agent; SELECT 1;"

# 4. 启动服务
./start_server.sh backend

# 5. 查看日志
tail -f logs/backend.log

# 6. 测试 API
curl http://localhost:8000/health
```

## 相关文件

- `init_database.sh` - 自动初始化脚本
- `init_database.sql` - SQL 初始化文件
- `.env` - 环境配置文件
- `api/models/user.py` - 数据库模型（自动创建表）
