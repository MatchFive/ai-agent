"""
用户数据模型
使用MySQL数据库 + aiomysql异步驱动
"""

import uuid
from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, select

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
    uid = Column(String(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)  # 绑定邮箱
    role = Column(String(20), default="user", nullable=False)  # admin / user
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, uid='{self.uid}', username='{self.username}', role='{self.role}')>"


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

    # 兼容已有表：检查并添加缺失的列
    try:
        from sqlalchemy import inspect as sa_inspect, text
        async with _engine.begin() as conn:
            def _get_columns(sync_conn):
                insp = sa_inspect(sync_conn)
                if 'conversations' in insp.get_table_names():
                    return [col['name'] for col in insp.get_columns('conversations')]
                return []
            columns = await conn.run_sync(_get_columns)
            if 'agent_name' not in columns:
                await conn.execute(text("ALTER TABLE conversations ADD COLUMN agent_name VARCHAR(100) DEFAULT NULL"))
            if 'title' not in columns:
                await conn.execute(text("ALTER TABLE conversations ADD COLUMN title VARCHAR(255) DEFAULT '新对话'"))
            # 检查 users 表是否有 email 列
            def _get_user_columns(sync_conn):
                insp = sa_inspect(sync_conn)
                if 'users' in insp.get_table_names():
                    return [col['name'] for col in insp.get_columns('users')]
                return []
            user_columns = await conn.run_sync(_get_user_columns)
            if 'email' not in user_columns:
                await conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE DEFAULT NULL"))
                logger.info("Added email column to users table")
    except Exception as e:
        logger.warning(f"数据库列迁移跳过: {e}")

    logger.info("Database tables created")

    # 创建默认管理员
    await create_default_admin()


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
            # 确保所有连接都被释放
            await _engine.dispose()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.warning(f"Error disposing database engine: {e}")
        finally:
            _engine = None

    logger.info("Database connections closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（用于依赖注入）"""
    if _async_session_factory is None:
        await init_db()

    async with _async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def get_session_factory():
    """获取异步会话工厂（供其他模块使用）"""
    return _async_session_factory


async def create_default_admin():
    """创建默认管理员账号并迁移现有用户"""
    global _async_session_factory

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with _async_session_factory() as session:
        # 迁移：为现有用户生成 uid
        result = await session.execute(select(User).where(User.uid == None))
        users_without_uid = result.scalars().all()
        for user in users_without_uid:
            user.uid = str(uuid.uuid4())
            logger.info(f"Generated uid for user: {user.username}")
        if users_without_uid:
            await session.commit()

        # 检查管理员是否已存在
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
