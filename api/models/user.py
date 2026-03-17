"""
用户数据模型
使用MySQL数据库 + aiomysql异步驱动
"""

from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, select
from sqlalchemy.pool import QueuePool

from core.config import settings
from core.logger import logger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 创建基类
Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # admin / user
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class InviteCode(Base):
    """邀请码表"""
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<InviteCode(id={self.id}, code='{self.code}', is_used={self.is_used})>"


# 数据库引擎和会话工厂
_engine = None
_async_session_factory = None


async def init_db():
    """初始化数据库连接"""
    global _engine, _async_session_factory

    if _engine is not None:
        return

    # 获取数据库URL
    db_url = settings.get_db_url()
    logger.info("Connecting to database...")

    # 创建异步引擎
    _engine = create_async_engine(
        db_url,
        echo=settings.db_echo,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    # 创建会话工厂
    _async_session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # 创建表
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created")

    # 创建默认管理员
    await create_default_admin()


async def close_db():
    """关闭数据库连接"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于依赖注入）"""
    global _async_session_factory

    if _async_session_factory is None:
        await init_db()

    async with _async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def create_default_admin():
    """创建默认管理员账号"""
    global _async_session_factory

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with _async_session_factory() as session:
        # 检查是否已存在
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username="admin",
                password_hash=pwd_context.hash("123456"),
                role="admin",
                is_active=True
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin created: admin / 123456")
