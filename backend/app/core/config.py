from typing import Optional

from pydantic import AliasChoices, Field
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
    # tuzi配置已弃用，请使用apiyi配置
    tuzi_api_key: str = ""
    tuzi_base_url: str = "https://api.tu-zi.com"

    # Apyi API配置 (主要配置)
    apiyi_api_key: str = ""
    apiyi_base_url: str = "https://api.apiyi.com"
    
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

    # GQCH API配置
    gqch_api_base_url: str = "https://gqch.haoee.com"
    gqch_api_key: str = ""

    # RunningHub API配置
    runninghub_api_base_url: str = "https://www.runninghub.cn"
    runninghub_api_key: str = ""
    runninghub_workflow_id_positioning: str = ""
    runninghub_positioning_node_id: str = "78"
    runninghub_positioning_field_name: str = "image"
    runninghub_workflow_id_vr2: str = ""
    runninghub_vr2_node_id: str = "53"
    runninghub_vr2_field_name: str = "image"
    runninghub_workflow_id_rh_double_1480: str = ""
    runninghub_rh_double_1480_node_id: str = "130,183"
    runninghub_rh_double_1480_field_name: str = "image"
    runninghub_workflow_id_rh_double_1800: str = ""
    runninghub_rh_double_1800_node_id: str = "130,183"
    runninghub_rh_double_1800_field_name: str = "image"
    # 提取花型通用1 专用工作流（返回单张）
    runninghub_workflow_id_extract_general1_1: str = ""
    runninghub_extract_general1_node_id_1: str = ""
    runninghub_extract_general1_field_name_1: str = "image"
    runninghub_workflow_id_extract_general1_2: str = ""
    runninghub_extract_general1_node_id_2: str = ""
    runninghub_extract_general1_field_name_2: str = "image"
    runninghub_workflow_id_extract_general1_3: str = ""
    runninghub_extract_general1_node_id_3: str = ""
    runninghub_extract_general1_field_name_3: str = "image"
    runninghub_workflow_id_extract_general1_4: str = ""
    runninghub_extract_general1_node_id_4: str = ""
    runninghub_extract_general1_field_name_4: str = "image"
    runninghub_poll_interval_seconds: int = 5
    runninghub_poll_timeout_seconds: int = 600

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

    # 微信支付配置
    wechat_app_id: str = ""
    wechat_mch_id: str = ""
    wechat_api_key: str = ""
    wechat_sandbox: bool = True

    # 支付宝配置
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""
    alipay_sandbox: bool = True

    # 拉卡拉聚合收银台配置
    lakala_api_base_url: str = "https://test.wsmsd.cn/sit"
    lakala_api_schema: str = "LKLAPI-SHA256withRSA"
    lakala_api_version: str = "3.0"
    lakala_app_id: str = "OP00000003"
    lakala_serial_no: str = "00dfba8194c41b84cf"
    lakala_merchant_no: str = "82229007392000A"
    lakala_term_no: str = "D9296400"
    lakala_private_key_path: str = "./assets/OP00000003_private_key.pem"
    lakala_certificate_path: str = "./assets/lkl-apigw-v2.cer"
    lakala_notify_certificate_path: Optional[str] = "./assets/OP00000003_cert.cer"
    lakala_sm4_key: Optional[str] = "LHo55AjrT4aDhAIBZhb5KQ=="
    lakala_default_timeout: int = 10
    lakala_skip_signature_verification: bool = False

    # 基础URL配置
    base_url: str = "http://localhost:8000"

    # 邮件配置
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: str = "noreply@loom-ai.com"

    # 短信服务配置
    sms_access_key: str = Field(
        default="",
        validation_alias=AliasChoices("SMS_ACCESS_KEY", "ALIBABA_CLOUD_ACCESS_KEY_ID"),
    )
    sms_access_key_secret: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SMS_ACCESS_KEY_SECRET",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        ),
    )
    sms_sign_name: str = "广州阳羚科技"
    sms_template_code: str = "SMS_498205525"
    sms_region: str = "cn-hangzhou"
    sms_mock_enabled: bool = False
    sms_code_valid_minutes: int = 5
    environment: str = "development"  # development or production

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS配置
    allowed_origins: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "https://loom-ai.com",
        "https://www.loom-ai.com",
        "https://tuyun.website",
        "https://www.tuyun.website",
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
