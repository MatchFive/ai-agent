# AI-Agent 快速使用指南

## 一键部署

```bash
# 1. 运行快速部署脚本（自动安装依赖、构建前端、设置权限）
bash quick_setup.sh

# 2. 配置环境变量
cp .env.example .env
vi .env

# 3. 初始化数据库（重要！）
bash init_database.sh

# 4. 启动服务
./start_server.sh all prod
```

## 服务管理

### 启动服务

```bash
# 生产模式启动所有服务
./start_server.sh all prod

# 开发模式启动所有服务（带热重载）
./start_server.sh all dev

# 单独启动
./start_server.sh backend      # 后端
./start_server.sh user dev     # 用户端（开发模式）
./start_server.sh admin prod   # 管理端（生产模式）
```

### 停止服务

```bash
# 停止所有服务
./stop_server.sh all

# 查看服务状态
./stop_server.sh status

# 强制停止所有进程（清理异常进程）
./stop_server.sh force
```

### 构建前端

```bash
# 构建所有前端项目
./build.sh all

# 单独构建
./build.sh user      # 用户端
./build.sh admin     # 管理端
```

## 访问地址

### 生产环境

- 后端 API: `http://YOUR_IP:8000`
- API 文档: `http://YOUR_IP:8000/docs`
- 用户端: 通过 Nginx 访问（推荐）
- 管理端: 通过 Nginx 访问（推荐）

### 开发环境

- 后端 API: `http://localhost:8000`
- API 文档: `http://localhost:8000/docs`
- 用户端: `http://localhost:3000`
- 管理端: `http://localhost:3001`

## 日志查看

```bash
# 查看所有日志
tail -f logs/*.log

# 查看后端日志
tail -f logs/backend.log

# 查看用户端日志
tail -f logs/user.log

# 查看管理端日志
tail -f logs/admin.log
```

## 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
lsof -i:8000
lsof -i:3000
lsof -i:3001

# 强制停止所有进程
./stop_server.sh force
```

### 2. 服务启动失败

```bash
# 查看日志
tail -f logs/backend.log

# 检查环境
python --version
node --version
npm --version
```

### 3. 前端构建失败

```bash
# 手动安装依赖并构建
cd frontend/user
npm install
npm run build
```

### 4. 权限问题

```bash
# 给脚本添加执行权限
chmod +x quick_setup.sh start_server.sh stop_server.sh build.sh init_database.sh
```

### 5. 数据库权限错误

**错误信息**: `SELECT command denied to user 'ai_agent'@'localhost'`

**解决方案**:

```bash
# 运行数据库初始化脚本
bash init_database.sh

# 或手动执行
mysql -u root -p < init_database.sql
```

详细说明请查看: `docs/DATABASE_PERMISSION_FIX.md`

## 目录结构

```
ai-agent/
├── quick_setup.sh          # 一键部署脚本
├── start_server.sh         # 启动服务
├── stop_server.sh          # 停止服务
├── build.sh                # 构建前端
├── logs/                    # 日志目录
│   ├── backend.log
│   ├── user.log
│   ├── admin.log
│   └── *.pid               # 进程ID文件
├── frontend/               # 前端项目
│   ├── user/              # 用户端
│   │   └── dist/          # 构建输出
│   └── admin/             # 管理端
│       └── dist/          # 构建输出
└── api/                    # 后端代码
```

## 端口说明

| 服务 | 端口 | 说明 |
|-----|------|------|
| 后端 API | 8000 | FastAPI 后端服务 |
| 用户端 | 3000 | 用户端前端（生产模式） |
| 管理端 | 3001 | 管理端前端（生产模式） |

**注意**: 开发模式下端口可能不同（Vite 默认 5173/5174）

## 生产环境建议

1. **使用 Nginx 反向代理**
   - 不要直接暴露 3000/3001 端口
   - 配置 SSL 证书启用 HTTPS
   - 配置静态资源缓存

2. **配置防火墙**
   ```bash
   # CentOS/RHEL
   sudo firewall-cmd --permanent --add-port=8000/tcp
   sudo firewall-cmd --reload

   # Ubuntu/Debian
   sudo ufw allow 8000/tcp
   ```

3. **设置开机自启**（可选）
   - 使用 systemd 管理服务

4. **定期备份数据库**

5. **监控服务状态**
   ```bash
   # 添加到 crontab
   */5 * * * * /path/to/stop_server.sh status
   ```

## 技术支持

如遇到问题，请：
1. 查看服务状态: `./stop_server.sh status`
2. 查看日志文件: `tail -f logs/*.log`
3. 检查端口占用: `lsof -i:端口号`
4. 检查进程: `ps aux | grep uvicorn`
