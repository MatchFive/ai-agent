"""
配置管理模块
"""

import os
from pathlib import Path
from typing import Optional, List

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """LLM配置"""
    provider: str = Field(default="anthropic", description="LLM提供商")
    model: str = Field(default="claude-sonnet-4-6", description="模型名称")
    api_key: str = Field(default="", description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    max_tokens: int = Field(default=4096, description="最大token数")
    temperature: float = Field(default=0.7, description="温度参数")

    class Config:
        env_prefix = "LLM_"


class EmailSettings(BaseSettings):
    """邮件配置"""
    smtp_host: str = Field(default="smtp.example.com", description="SMTP服务器")
    smtp_port: int = Field(default=587, description="SMTP端口")
    username: str = Field(default="", description="邮箱用户名")
    password: str = Field(default="", description="邮箱密码")
    from_addr: str = Field(default="", description="发件人地址")
    use_tls: bool = Field(default=True, description="使用TLS")

    class Config:
        env_prefix = "EMAIL_"


class SchedulerSettings(BaseSettings):
    """调度器配置"""
    backend: str = Field(default="memory", description="存储后端")
    redis_url: Optional[str] = Field(default=None, description="Redis连接URL")

    class Config:
        env_prefix = "SCHEDULER_"


class DatabaseSettings(BaseSettings):
    """数据库配置 - MySQL"""
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=3306, description="数据库端口")
    user: str = Field(default="root", description="数据库用户")
    password: str = Field(default="", description="数据库密码")
    database: str = Field(default="ai_agent", description="数据库名称")
    url: Optional[str] = Field(default=None, description="完整数据库URL(优先)")
    echo: bool = Field(default=False, description="SQL日志")
    charset: str = Field(default="utf8mb4", description="字符集")

    class Config:
        env_prefix = "DB_"

    def get_url(self) -> str:
        """获取数据库连接URL"""
        if self.url:
            return self.url
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"


class Settings(BaseSettings):
    """主配置类"""

    # 应用配置
    app_name: str = Field(default="AI-Agent", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    secret_key: str = Field(default="ai-agent-secret-key-change-in-production", description="JWT密钥")

    # 子配置
    llm: LLMSettings = Field(default_factory=LLMSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


def load_yaml_config(config_path: str = "config/settings.yaml") -> dict:
    """加载YAML配置文件"""
    path = Path(config_path)
    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def create_settings() -> Settings:
    """创建配置实例，合并YAML和环境变量"""
    yaml_config = load_yaml_config()

    # 环境变量优先级高于YAML
    settings = Settings()

    # 应用YAML配置（如果存在）
    if yaml_config:
        if "llm" in yaml_config:
            for k, v in yaml_config["llm"].items():
                if not os.environ.get(f"LLM_{k.upper()}"):
                    setattr(settings.llm, k, v)
        if "email" in yaml_config:
            for k, v in yaml_config["email"].items():
                if not os.environ.get(f"EMAIL_{k.upper()}"):
                    setattr(settings.email, k, v)
        if "scheduler" in yaml_config:
            for k, v in yaml_config["scheduler"].items():
                if not os.environ.get(f"SCHEDULER_{k.upper()}"):
                    setattr(settings.scheduler, k, v)
        if "database" in yaml_config:
            for k, v in yaml_config["database"].items():
                if not os.environ.get(f"DB_{k.upper()}"):
                    setattr(settings.database, k, v)

    return settings


# 全局配置实例
settings = create_settings()
