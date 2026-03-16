"""
FastAPI 主入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import logger
from api.models.user import init_db, close_db
from api.routers import auth_router, admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("Starting AI-Agent API...")
    logger.info(f"Database: {settings.database.host}:{settings.database.port}/{settings.database.database}")
    await init_db()
    logger.info("Database initialized")

    yield

    # 关闭时
    logger.info("Shutting down AI-Agent API...")
    await close_db()
    logger.info("Database connections closed")


# 创建应用
app = FastAPI(
    title="AI-Agent API",
    description="多Agent集成系统API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AI-Agent API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
