"""
用户数据模型
使用MySQL数据库 + pymysql连接库
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.pool import QueuePool

from core.config import settings
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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    invite_codes = relationship("InviteCode", back_populates="creator", foreign_keys="InviteCode.created_by")
    used_codes = relationship("InviteCode", back_populates="user", foreign_keys="InviteCode.used_by")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class InviteCode(Base):
    """邀请码表"""
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)

    # 关联
    creator = relationship("User", back_populates="invite_codes", foreign_keys=[created_by])
    user = relationship("User", back_populates="used_codes", foreign_keys=[used_by])

    def __repr__(self):
        return f"<InviteCode(id={self.id}, code='{self.code}', is_used={self.is_used})>"


# 数据库引擎和会话
engine = None
async_session_maker = None


async def init_db():
    """初始化数据库"""
    global engine, async_session_maker

    # MySQL连接配置
    # 使用 aiomysql 作为异步驱动
    db_url = settings.database.url

    # 如果URL以mysql://开头，转换为mysql+aiomysql://
    if db_url.startswith("mysql://"):
        db_url = db_url.replace("mysql://", "mysql+aiomysql://")
    elif db_url.startswith("mysql+pymysql://"):
        db_url = db_url.replace("mysql+pymysql://", "mysql+aiomysql://")

    engine = create_async_engine(
        db_url,
        echo=settings.database.echo,
        poolclass=QueuePool,
        pool_size=10,           # 连接池大小
        max_overflow=20,        # 最大溢出连接数
        pool_timeout=30,        # 获取连接超时时间
        pool_recycle=3600,      # 连接回收时间(1小时)
        pool_pre_ping=True,     # 连接前检查可用性
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 创建默认管理员
    await create_default_admin()


async def get_session() -> AsyncSession:
    """获取数据库会话"""
    if async_session_maker is None:
        await init_db()
    return async_session_maker()


async def create_default_admin():
    """创建默认管理员账号"""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with async_session_maker() as session:
        # 检查是否已存在
        from sqlalchemy import select
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
            print("Default admin created: admin / 123456")


async def close_db():
    """关闭数据库连接"""
    global engine
    if engine:
        await engine.dispose()
        engine = None
