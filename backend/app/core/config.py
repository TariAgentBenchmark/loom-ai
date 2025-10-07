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
    access_token_expire_minutes: int = 10080  # 7天 = 7 * 24 * 60 = 10080分钟
    refresh_token_expire_days: int = 7

    # 数据库配置
    database_url: str = "sqlite:///./data/loom_ai.db"
    sqlalchemy_echo: bool = False

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # 第三方API配置
    tuzi_api_key: str = ""
    tuzi_base_url: str = "https://api.tu-zi.com"
    
    # 美图API配置
    meitu_api_key: str = ""
    meitu_api_secret: str = ""
    meitu_base_url: str = "https://openapi.meitu.com"
    
    # Dewatermark.ai API配置
    dewatermark_api_key: str = ""
    
    # Vectorizer.ai API配置
    vectorizer_api_key: str = ""
    vectorizer_api_secret: str = ""
    
    # 即梦API配置
    jimeng_api_key: str = ""
    jimeng_api_secret: str = ""
    jimeng_base_url: str = "https://visual.volcengineapi.com"
    
    # Liblib AI API配置
    liblib_api_url: str = "https://openapi.liblibai.cloud"
    liblib_template_uuid: str = "4df2efa0f18d46dc9758803e478eb51c"
    liblib_workflow_uuid: str = "18d5858e862d474abe93c72b2fb1b8cc"
    liblib_access_key: str = ""
    liblib_secret_key: str = ""

    # 阿里云OSS配置
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_endpoint: str = "https://oss-cn-hangzhou.aliyuncs.com"
    oss_bucket_name: str = ""
    oss_bucket_domain: str = ""
    oss_expiration_time: int = 3600  # URL过期时间（秒）

    # 文件存储配置
    upload_path: str = "./uploads"
    max_file_size: int = 52428800  # 50MB
    allowed_extensions: str = "png,jpg,jpeg,gif,bmp,webp,svg"

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