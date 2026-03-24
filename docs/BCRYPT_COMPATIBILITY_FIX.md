# 快速修复 bcrypt 兼容性问题

## 问题

```
(trapped) error reading bcrypt version
ValueError: password cannot be longer than 72 bytes
```

## 快速修复

```bash
# 在服务器上运行
chmod +x fix_bcrypt.sh
bash fix_bcrypt.sh

# 重启服务
./stop_server.sh backend
./start_server.sh backend
```

## 详细说明

查看 [BCRYPT_COMPATIBILITY_FIX.md](./BCRYPT_COMPATIBILITY_FIX.md)
