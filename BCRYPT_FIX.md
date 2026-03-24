# bcrypt 兼容性问题快速修复

## 问题症状

```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
```

## 快速修复

### 在服务器上执行：

```bash
# 1. 运行修复脚本
chmod +x fix_bcrypt.sh
bash fix_bcrypt.sh

# 2. 重启后端服务
./stop_server.sh backend
./start_server.sh backend

# 3. 查看日志
tail -f logs/backend.log
```

### 手动修复：

```bash
# 激活环境
conda activate ai_agent

# 降级 bcrypt
pip uninstall -y bcrypt
pip install 'bcrypt>=4.0.1,<4.1.0'

# 重启服务
./stop_server.sh backend
./start_server.sh backend
```

## 问题原因

- bcrypt 4.1+ 与 passlib 1.7.4 不兼容
- bcrypt 4.1 移除了 `__about__` 模块
- 需要使用 bcrypt 4.0.x

## 详细文档

查看 [docs/BCRYPT_COMPATIBILITY_FIX.md](./docs/BCRYPT_COMPATIBILITY_FIX.md)
