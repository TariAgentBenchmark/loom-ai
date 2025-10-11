import logging
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from app.core.config import settings
from app.models.user import User
from app.services.aliyun_sms import AliyunSMSClient


logger = logging.getLogger(__name__)


class SMSService:
    """短信服务"""
    
    def __init__(self):
        # 初始化短信服务配置
        self.access_key = getattr(settings, 'sms_access_key', '')
        self.access_key_secret = getattr(settings, 'sms_access_key_secret', '')
        self.sign_name = getattr(settings, 'sms_sign_name', 'LoomAI')
        self.template_code = getattr(settings, 'sms_template_code', 'SMS_123456789')
        self.environment = getattr(settings, 'environment', 'development')
        self.region_id = getattr(settings, 'sms_region', 'cn-hangzhou')
        self.mock_enabled = getattr(settings, 'sms_mock_enabled', False)

        self._client: Optional[AliyunSMSClient] = None
        if self.access_key and self.access_key_secret:
            self._client = AliyunSMSClient(
                access_key_id=self.access_key,
                access_key_secret=self.access_key_secret,
                sign_name=self.sign_name,
                template_code=self.template_code,
                region_id=self.region_id,
            )
    
    def generate_verification_code(self) -> str:
        """生成6位数字验证码"""
        return str(random.randint(100000, 999999))
    
    def send_verification_sms(self, phone: str, code: str) -> bool:
        """发送验证码短信"""
        try:
            # 可选的模拟模式
            if self.mock_enabled:
                logger.info("[SMS Mock] 验证码发送至 %s: %s", phone, code)
                return True

            if not self._client:
                logger.error("短信服务未正确配置，缺少AccessKey或Secret")
                return False

            return self._client.send_sms(phone, {"code": code})
            
        except Exception as e:
            logger.exception("发送短信失败: %s", e)
            return False
    
    def can_send_sms(self, user: User) -> Tuple[bool, str]:
        """检查是否可以发送短信"""
        now = datetime.utcnow()
        
        # 检查是否在60秒内重复发送
        if user.last_sms_sent and (now - user.last_sms_sent).total_seconds() < 60:
            return False, "请等待60秒后再次发送"
        
        # 检查今日发送次数限制（例如每日10次）
        if user.last_sms_sent and user.last_sms_sent.date() == now.date():
            if user.sms_attempts_today >= 10:
                return False, "今日发送次数已达上限"
        else:
            # 重置每日计数
            user.sms_attempts_today = 0
        
        return True, ""
    
    def create_verification_record(self, user: User, db: Session) -> str:
        """创建验证码记录"""
        # 生成验证码
        code = self.generate_verification_code()
        expires = datetime.utcnow() + timedelta(minutes=5)  # 5分钟有效期
        
        # 更新用户验证信息
        user.phone_verification_code = code
        user.phone_verification_expires = expires
        user.last_sms_sent = datetime.utcnow()
        user.sms_attempts_today += 1
        
        db.commit()
        
        return code
    
    def verify_code(self, user: User, code: str, db: Session) -> bool:
        """验证验证码"""
        now = datetime.utcnow()
        
        # 检查验证码是否过期
        if not user.phone_verification_expires or user.phone_verification_expires < now:
            return False
        
        # 检查验证码是否正确
        if user.phone_verification_code != code:
            return False
        
        # 标记手机已验证
        user.is_phone_verified = True
        user.phone_verified_at = now
        user.phone_verification_code = None
        user.phone_verification_expires = None
        
        db.commit()
        
        return True
