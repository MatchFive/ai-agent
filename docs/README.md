# 文档目录

本目录包含项目的各种技术文档和故障排除指南。

## 文档列表

### 故障排除

- [AIOMYSQL_ERROR_FIX.md](./AIOMYSQL_ERROR_FIX.md) - aiomysql 事件循环关闭错误的解决方案

### 部署相关

部署相关文档已移到项目根目录，请查看：
- [QUICKSTART.md](../QUICKSTART.md) - 快速开始指南
- [DEPENDENCIES_UPDATE.md](../DEPENDENCIES_UPDATE.md) - 依赖更新说明
- [SCRIPT_MIGRATION.md](../SCRIPT_MIGRATION.md) - 脚本迁移说明

## 常见问题

### 1. 后端启动时出现 Event Loop 错误

**症状**: 看到 `RuntimeError: Event loop is closed` 错误

**解决**: 查看 [AIOMYSQL_ERROR_FIX.md](./AIOMYSQL_ERROR_FIX.md)

**简答**: 这是 aiomysql + Python 3.13 的已知问题，不影响功能，可以安全忽略。

### 2. 前端构建失败

**解决**:
```bash
cd frontend/user
rm -rf node_modules package-lock.json
npm install
npm run build
```

### 3. 服务无法启动

**检查步骤**:
1. 查看日志: `tail -f logs/backend.log`
2. 检查端口: `lsof -i:8000`
3. 检查依赖: `pip list | grep fastapi`
4. 查看状态: `./stop_server.sh status`

### 4. 数据库连接失败

**检查**:
1. 数据库是否运行
2. 配置文件中的连接信息是否正确
3. 防火墙是否开放数据库端口

## 获取帮助

1. 查看项目根目录的 [README.md](../README.md)
2. 查看日志文件
3. 运行诊断命令: `./stop_server.sh status`
