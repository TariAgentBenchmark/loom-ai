import logging
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, Tuple, Union

from app.core.config import settings
from app.models.user import User
from app.models.phone_verification import PhoneVerification
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
        self.code_valid_minutes = getattr(settings, 'sms_code_valid_minutes', 5)

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

            template_payload = {"code": code, "min": self.code_valid_minutes}
            return self._client.send_sms(phone, template_payload)
            
        except Exception as e:
            logger.exception("发送短信失败: %s", e)
            return False
    
    def get_or_create_phone_verification(self, db: Session, phone: str) -> PhoneVerification:
        """获取或创建手机号验证码记录"""
        record = db.query(PhoneVerification).filter(PhoneVerification.phone == phone).first()
        if record:
            return record

        record = PhoneVerification(phone=phone, sms_attempts_today=0)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def get_phone_verification(self, db: Session, phone: str) -> Optional[PhoneVerification]:
        """获取手机号验证码记录"""
        return db.query(PhoneVerification).filter(PhoneVerification.phone == phone).first()

    def can_send_sms(self, target: Union[User, PhoneVerification]) -> Tuple[bool, str]:
        """检查是否可以发送短信"""
        now = datetime.utcnow()
        
        # 检查是否在60秒内重复发送
        if target.last_sms_sent and (now - target.last_sms_sent).total_seconds() < 60:
            return False, "请等待60秒后再次发送"
        
        # 检查今日发送次数限制（例如每日10次）
        if target.last_sms_sent and target.last_sms_sent.date() == now.date():
            if target.sms_attempts_today >= 10:
                return False, "今日发送次数已达上限"
        else:
            # 重置每日计数
            target.sms_attempts_today = 0
        
        return True, ""
    
    def create_verification_record(self, target: Union[User, PhoneVerification], db: Session) -> str:
        """创建验证码记录"""
        # 生成验证码
        code = self.generate_verification_code()
        expires = datetime.utcnow() + timedelta(minutes=self.code_valid_minutes)
        
        # 更新用户验证信息
        target.phone_verification_code = code
        target.phone_verification_expires = expires
        target.last_sms_sent = datetime.utcnow()
        if target.sms_attempts_today is None:
            target.sms_attempts_today = 0
        target.sms_attempts_today += 1
        if isinstance(target, PhoneVerification):
            target.is_phone_verified = False
            target.phone_verified_at = None
        
        db.commit()
        
        return code
    
    def verify_code(self, target: Union[User, PhoneVerification], code: str, db: Session) -> bool:
        """验证验证码"""
        now = datetime.utcnow()
        
        # 检查验证码是否过期
        if not target.phone_verification_expires or target.phone_verification_expires < now:
            return False
        
        # 检查验证码是否正确
        if target.phone_verification_code != code:
            return False
        
        # 标记手机已验证
        target.is_phone_verified = True
        target.phone_verified_at = now
        target.phone_verification_code = None
        target.phone_verification_expires = None
        
        db.commit()
        
        return True
