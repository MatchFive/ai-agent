# 脚本调整说明

## 变更内容

为了方便服务器部署，将所有脚本统一移动到项目根目录，`deploy/` 目录不提交到远程仓库。

### 文件移动

- `deploy/build.sh` → `build.sh`
- `deploy/quick_setup.sh` → `quick_setup.sh`

### 脚本位置

现在所有管理脚本都在项目根目录：

```
ai-agent/
├── quick_setup.sh      # 一键部署脚本
├── start_server.sh     # 启动服务
├── stop_server.sh      # 停止服务
├── build.sh            # 构建前端
└── init_env.sh         # 环境初始化
```

### 使用方式

#### 在服务器上首次部署

```bash
# 1. 克隆代码后，运行一键部署
bash quick_setup.sh

# 2. 配置环境变量
cp .env.example .env
vi .env

# 3. 启动服务
./start_server.sh all prod
```

#### 日常管理

```bash
# 启动服务
./start_server.sh all prod

# 停止服务
./stop_server.sh all

# 查看状态
./stop_server.sh status

# 构建前端
./build.sh all
```

### deploy/ 目录说明

`deploy/` 目录仅用于本地开发，包含：
- Nginx 配置文件示例
- 部署文档
- 其他部署相关资源

这些文件不会提交到 Git，如需使用请手动复制到服务器。

### 文档位置

- **快速开始**: `QUICKSTART.md`
- **详细文档**: `README.md`

## .gitignore 更新

`deploy/` 目录已在 `.gitignore` 中排除，不会提交到远程仓库。

## 注意事项

1. **首次使用需要给脚本执行权限**
   ```bash
   chmod +x quick_setup.sh start_server.sh stop_server.sh build.sh
   ```

2. **deploy 目录的 Nginx 配置**
   - 本地保留 `deploy/nginx/` 配置文件作为参考
   - 服务器部署时手动复制或参考配置

3. **路径变更**
   - 所有脚本现在从项目根目录运行
   - 脚本内部路径已全部更新

## 测试建议

在服务器上测试：

```bash
# 1. 运行一键部署
bash quick_setup.sh

# 2. 检查服务状态
./stop_server.sh status

# 3. 测试启动
./start_server.sh all prod

# 4. 测试停止
./stop_server.sh all

# 5. 测试构建
./build.sh all
```
