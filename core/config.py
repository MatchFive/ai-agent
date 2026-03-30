"""
配置管理模块 - 简化版
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略未定义的环境变量
        case_sensitive=False,
    )

    # 应用配置
    app_name: str = Field(default="AI-Agent", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    secret_key: str = Field(
        default="ai-agent-secret-key-change-in-production",
        description="JWT密钥"
    )

    # LLM配置
    llm_provider: str = Field(default="openai", description="LLM提供商")
    llm_model: str = Field(default="deepseek-chat", description="模型名称")
    llm_api_key: str = Field(default="", description="API密钥")
    llm_base_url: Optional[str] = Field(default=None, description="API基础URL")
    llm_max_tokens: int = Field(default=4096, description="最大token数")
    llm_temperature: float = Field(default=0.7, description="温度参数")

    # 邮件配置
    email_smtp_host: str = Field(default="smtp.example.com")
    email_smtp_port: int = Field(default=587)
    email_username: str = Field(default="")
    email_password: str = Field(default="")
    email_from: str = Field(default="")
    email_use_tls: bool = Field(default=True)

    # 调度器配置
    scheduler_backend: str = Field(default="memory")
    scheduler_redis_url: Optional[str] = Field(default=None)

    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")

    # Embedding 配置
    embedding_base_url: str = Field(default="http://localhost:8000/v1/embeddings", description="Embedding服务地址")
    embedding_model: str = Field(default="/models/Qwen/Qwen3-Embedding-0___6B/", description="Embedding模型")
    embedding_batch_size: int = Field(default=128, description="Embedding批量大小")

    # Milvus 配置
    milvus_host: str = Field(default="localhost", description="Milvus地址")
    milvus_port: int = Field(default=19530, description="Milvus端口")
    milvus_dim: int = Field(default=1024, description="向量维度")

    # 数据库配置 - MySQL
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=3306)
    db_user: str = Field(default="root")
    db_password: str = Field(default="")
    db_database: str = Field(default="ai_agent")
    db_url: Optional[str] = Field(default=None, description="完整数据库URL(优先)")
    db_echo: bool = Field(default=False, description="SQL日志")
    db_charset: str = Field(default="utf8mb4")

    def get_db_url(self) -> str:
        """获取数据库连接URL"""
        if self.db_url:
            # 转换为异步URL
            url = self.db_url
            if url.startswith("mysql://"):
                url = url.replace("mysql://", "mysql+aiomysql://")
            elif url.startswith("mysql+pymysql://"):
                url = url.replace("mysql+pymysql://", "mysql+aiomysql://")
            return url
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
            f"?charset={self.db_charset}"
        )


# 全局配置实例
settings = Settings()
