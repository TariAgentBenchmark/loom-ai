from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class PhoneVerification(Base):
    """手机号验证码记录"""
    __tablename__ = "phone_verifications"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    phone_verification_code = Column(String(10), nullable=True)
    phone_verification_expires = Column(DateTime, nullable=True)
    is_phone_verified = Column(Boolean, default=False)
    phone_verified_at = Column(DateTime, nullable=True)
    last_sms_sent = Column(DateTime, nullable=True)
    sms_attempts_today = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
