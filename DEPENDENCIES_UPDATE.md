# 依赖更新说明

## 更新日期
2026-03-23

## Python 依赖更新 (requirements.txt)

### 核心依赖

| 包名 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| anthropic | >=0.40.0 | >=0.45.0 | Claude API SDK |
| pydantic | >=2.0.0 | >=2.9.0 | 数据验证 |
| pydantic-settings | >=2.0.0 | >=2.5.0 | 配置管理 |
| pyyaml | >=6.0 | >=6.0.2 | YAML 解析 |
| apscheduler | >=3.10.0 | >=3.10.4 | 任务调度 |
| httpx | >=0.27.0 | >=0.28.0 | HTTP 客户端 |

### 数据库相关

| 包名 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| sqlalchemy | >=2.0.0 | >=2.0.36 | ORM |
| pymysql | >=1.1.0 | >=1.1.1 | MySQL 驱动 |
| aiomysql | >=0.2.0 | >=0.2.0 | 异步 MySQL 驱动 |

### FastAPI 相关

| 包名 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| fastapi | >=0.110.0 | >=0.115.0 | Web 框架 |
| uvicorn | >=0.27.0 | >=0.32.0 | ASGI 服务器 |
| python-multipart | >=0.0.9 | >=0.0.12 | 文件上传支持 |

### 认证相关

| 包名 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| passlib | >=1.7.4 | >=1.7.4 | 密码哈希 |
| bcrypt | >=4.1.0 | >=4.2.1 | 密码加密 |
| pyjwt | >=2.8.0 | >=2.10.0 | JWT 认证 |

### 工具类

| 包名 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| loguru | >=0.7.0 | >=0.7.2 | 日志 |
| python-dotenv | >=1.0.0 | - | 移除（使用 pydantic-settings） |
| rich | >=13.0.0 | >=13.9.0 | 终端美化 |
| asyncio-throttle | >=1.0 | >=1.0 | 异步限流 |

### 新增依赖

| 包名 | 版本 | 说明 |
|-----|------|------|
| sqlalchemy | >=2.0.36 | 明确版本 |
| aiomysql | >=0.2.0 | 异步数据库支持 |

### 移除的依赖

| 包名 | 原因 |
|-----|------|
| python-dotenv | 使用 pydantic-settings 替代 |

## Node.js 依赖更新 (package.json)

### 用户端和管理端通用更新

| 包名 | 旧版本 | 新版本 | 说明 |
|-----|--------|--------|------|
| vue | ^3.4.0 | ^3.5.0 | Vue 3 框架 |
| vue-router | ^4.2.0 | ^4.4.0 | 路由 |
| pinia | ^2.1.0 | ^2.2.0 | 状态管理 |
| axios | ^1.6.0 | ^1.7.0 | HTTP 客户端 |
| element-plus | ^2.5.0 | ^2.8.0 | UI 组件库 |
| @vitejs/plugin-vue | ^5.0.0 | ^5.2.0 | Vite Vue 插件 |
| vite | ^5.0.0 | ^6.0.0 | 构建工具 |

### 管理端新增配置

```json
{
  "type": "module"
}
```

## 如何更新依赖

### Python 依赖

```bash
# 1. 激活虚拟环境
conda activate ai_agent
# 或
source venv/bin/activate

# 2. 更新所有依赖
pip install -r requirements.txt --upgrade

# 3. 查看已安装的版本
pip list

# 4. 生成依赖锁定文件（可选）
pip freeze > requirements.lock
```

### Node.js 依赖

```bash
# 用户端
cd frontend/user
rm -rf node_modules package-lock.json
npm install

# 管理端
cd frontend/admin
rm -rf node_modules package-lock.json
npm install
```

## 兼容性说明

### Python 版本要求
- **最低版本**: Python 3.10+
- **推荐版本**: Python 3.12+

### Node.js 版本要求
- **最低版本**: Node.js 18.x
- **推荐版本**: Node.js 20.x LTS

## 主要变更和注意事项

### 1. Pydantic v2 升级
- 已升级到 Pydantic 2.9.0
- 确保所有模型兼容 Pydantic v2

### 2. FastAPI 升级到 0.115.0
- 改进的性能
- 更好的异步支持
- 新的生命周期事件

### 3. Vue 3.5 升级
- 性能提升
- 更好的响应式系统
- 新的 Composition API 特性

### 4. Vite 6.0 升级
- 构建速度提升
- 更好的 Tree-shaking
- 改进的 HMR

### 5. Element Plus 2.8.0
- 新组件
- Bug 修复
- 性能优化

## 测试建议

更新依赖后，建议进行以下测试：

### 1. 后端测试

```bash
# 启动后端
python -m uvicorn api.main:app --reload

# 测试 API
curl http://localhost:8000/docs
```

### 2. 前端测试

```bash
# 用户端
cd frontend/user
npm run dev

# 管理端
cd frontend/admin
npm run dev
```

### 3. 构建测试

```bash
# 构建前端
./build.sh all

# 启动所有服务
./start_server.sh all prod
```

## 回滚方案

如果更新后出现问题，可以回滚到旧版本：

### Python 依赖回滚

```bash
# 使用旧版本的 requirements.txt
git checkout HEAD~1 requirements.txt
pip install -r requirements.txt
```

### Node.js 依赖回滚

```bash
# 使用旧版本的 package.json
git checkout HEAD~1 frontend/user/package.json
git checkout HEAD~1 frontend/admin/package.json

# 重新安装
cd frontend/user && npm install
cd ../admin && npm install
```

## 已知问题

### 1. SQLAlchemy 2.0 兼容性
- 异步引擎不支持 QueuePool（已修复）
- 使用 AsyncAdaptedQueuePool 或不指定 poolclass

### 2. Vite 6.0 变更
- 需要在 package.json 中添加 `"type": "module"`
- 配置文件格式可能有变化

### 3. Element Plus 图标
- 可能需要重新导入图标
- 检查图标组件使用

## 安全更新

此次更新包含以下安全修复：
- bcrypt: 修复潜在的安全漏洞
- pyjwt: 安全性增强
- axios: 修复 SSRF 漏洞
- vite: 修复开发服务器安全问题

## 下一步计划

1. ✅ 更新依赖版本
2. ⏳ 运行测试套件
3. ⏳ 检查兼容性问题
4. ⏳ 更新文档
5. ⏳ 性能测试

## 参考资料

- [FastAPI 发布说明](https://fastapi.tiangolo.com/release-notes/)
- [Vue 3.5 发布说明](https://blog.vuejs.org/posts/vue-3-5)
- [Vite 6.0 迁移指南](https://vitejs.dev/guide/migration.html)
- [Pydantic v2 文档](https://docs.pydantic.dev/latest/)
