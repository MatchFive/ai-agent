# aiomysql Event Loop 错误解决方案

## 问题描述

在启动后端服务时，可能会看到以下警告信息：

```
Exception ignored in: <function Connection.__del__ at 0x76738cbd99e0>
Traceback (most recent call last):
  File "/root/anaconda3/envs/ai_agent/lib/python3.13/site-packages/aiomysql/connection.py", line 1131, in __del__
  File "/root/anaconda3/envs/ai_agent/lib/python3.13/site-packages/aiomysql/connection.py", line 339, in close
  ...
RuntimeError: Event loop is closed
```

## 原因分析

这是 aiomysql 在 Python 3.13 中的一个已知问题：

1. **根本原因**: 当应用程序退出时，aiomysql 的连接对象在 `__del__` 析构方法中尝试关闭连接
2. **时序问题**: 此时 Python 的事件循环已经关闭，导致无法正确关闭连接
3. **影响范围**: 这只是一个警告，**不影响实际功能**，服务可以正常运行

## 已实施的解决方案

### 1. 改进数据库连接关闭逻辑

在 `api/models/user.py` 中的 `close_db()` 函数已改进：

```python
async def close_db():
    """关闭数据库连接"""
    global _engine, _async_session_factory

    # 先关闭会话工厂
    if _async_session_factory:
        _async_session_factory = None
        logger.info("Database session factory closed")

    # 然后关闭引擎和连接池
    if _engine:
        try:
            await _engine.dispose()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.warning(f"Error disposing database engine: {e}")
        finally:
            _engine = None

    logger.info("Database connections closed")
```

### 2. 改进 uvicorn 启动参数

在 `start_server.sh` 中添加了 `--timeout-keep-alive 30` 参数，确保连接有足够时间关闭。

## 可选的额外解决方案

如果仍然看到这个警告，可以考虑以下方案：

### 方案 1：忽略警告（推荐）

这个警告不影响功能，可以选择忽略。服务可以正常使用。

### 方案 2：使用环境变量抑制警告

在启动脚本中添加环境变量：

```bash
export PYTHONWARNINGS="ignore::RuntimeError"
```

### 方案 3：切换到 asyncmy（替代方案）

如果问题严重影响使用，可以考虑将 aiomysql 替换为 asyncmy：

```bash
# 安装 asyncmy
pip install asyncmy

# 修改 requirements.txt
# 将 aiomysql>=0.2.0 改为 asyncmy>=0.2.9

# 修改数据库连接 URL
# 将 mysql+aiomysql:// 改为 mysql+asyncmy://
```

### 方案 4：降级到 Python 3.12

如果使用 Python 3.13，可以考虑降级到 Python 3.12：

```bash
# 创建新的 conda 环境
conda create -n ai_agent_py312 python=3.12
conda activate ai_agent_py312
pip install -r requirements.txt
```

## 验证服务正常

尽管有这个警告，服务应该可以正常运行。验证方法：

```bash
# 1. 启动服务
./start_server.sh backend

# 2. 检查服务状态
./stop_server.sh status

# 3. 测试 API
curl http://localhost:8000/health
# 应该返回: {"status": "healthy"}

# 4. 查看 API 文档
# 访问 http://YOUR_IP:8000/docs

# 5. 查看日志
tail -f logs/backend.log
```

## 最佳实践

### 1. 确保正确关闭连接

始终在应用生命周期中正确关闭数据库连接：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()  # 确保调用
```

### 2. 使用连接池

确保 SQLAlchemy 引擎使用连接池：

```python
_engine = create_async_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

### 3. 正确使用会话

使用 `async with` 确保会话正确关闭：

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        # 会话会自动关闭
```

## 监控和日志

### 查看服务状态

```bash
# 查看进程
ps aux | grep uvicorn

# 查看端口
lsof -i:8000

# 查看服务状态
./stop_server.sh status
```

### 查看详细日志

```bash
# 实时日志
tail -f logs/backend.log

# 搜索错误
grep -i error logs/backend.log
grep -i exception logs/backend.log

# 查看最近的错误
tail -n 100 logs/backend.log | grep -i error
```

## 相关问题

### Q1: 这个警告会影响性能吗？

**A**: 不会。这只是一个退出时的清理警告，不影响运行时性能。

### Q2: 数据会丢失吗？

**A**: 不会。数据库操作已经正确提交或回滚，这个警告只是连接清理问题。

### Q3: 需要立即修复吗？

**A**: 不需要。这是一个已知问题，可以安全忽略。如果想要消除警告，可以考虑上述方案。

### Q4: 在生产环境会有问题吗？

**A**: 不会有问题。服务可以正常运行和提供服务。

## 参考资料

- [aiomysql GitHub Issue #857](https://github.com/aio-libs/aiomysql/issues/857)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

## 总结

1. ✅ 这个警告是 aiomysql + Python 3.13 的已知问题
2. ✅ 不影响服务功能和性能
3. ✅ 已改进数据库连接关闭逻辑
4. ✅ 服务可以正常使用
5. ⚠️ 如需完全消除警告，可考虑上述可选方案
