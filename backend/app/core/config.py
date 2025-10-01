from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    app_name: str = "LoomAI Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 数据库配置
    database_url: str = "sqlite:///./data/loom_ai.db"
    sqlalchemy_echo: bool = False

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # 第三方API配置
    tuzi_api_key: str = ""
    tuzi_base_url: str = "https://api.tu-zi.com"

    # 文件存储配置
    upload_path: str = "./uploads"
    max_file_size: int = 52428800  # 50MB
    allowed_extensions: str = "png,jpg,jpeg,gif,bmp,webp"

    # AWS S3配置 (可选)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_bucket_name: Optional[str] = None
    aws_region: str = "us-east-1"

    # 支付配置
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # 邮件配置
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@loom-ai.com"

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS配置
    allowed_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://loom-ai.com",
        "https://www.loom-ai.com",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",
    )

    @property
    def allowed_extensions_list(self) -> list:
        """获取允许的文件扩展名列表"""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]


# 创建全局配置实例
settings = Settings()