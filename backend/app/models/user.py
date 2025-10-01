from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class MembershipType(PyEnum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class UserStatus(PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)  # 用户唯一标识
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 账户信息
    credits = Column(Integer, default=0)  # 算力余额
    total_processed = Column(Integer, default=0)  # 总处理次数
    monthly_processed = Column(Integer, default=0)  # 本月处理次数
    
    # 会员信息
    membership_type = Column(Enum(MembershipType), default=MembershipType.FREE)
    membership_expiry = Column(DateTime, nullable=True)
    
    # 账户状态
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_email_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)  # 管理员标识
    email_verification_token = Column(String(255), nullable=True)
    
    # 密码重置
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # 通知设置 (JSON格式存储)
    notification_settings = Column(Text, nullable=True)  # JSON字符串
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    # 删除相关
    scheduled_deletion = Column(DateTime, nullable=True)
    deletion_reason = Column(String(500), nullable=True)
    
    # 关联关系
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, nickname={self.nickname})>"

    @property
    def is_premium_member(self) -> bool:
        """是否为付费会员"""
        return self.membership_type in [MembershipType.BASIC, MembershipType.PREMIUM, MembershipType.ENTERPRISE]

    @property
    def is_membership_active(self) -> bool:
        """会员是否有效"""
        if not self.is_premium_member:
            return False
        if not self.membership_expiry:
            return True  # 永久会员
        from datetime import datetime
        return self.membership_expiry > datetime.utcnow()

    def can_afford(self, credits_needed: int) -> bool:
        """检查是否有足够算力"""
        # 管理员用户有无限算力
        if self.is_admin:
            return True
        return self.credits >= credits_needed

    def deduct_credits(self, amount: int) -> bool:
        """扣除算力"""
        # 管理员用户不需要扣除算力
        if self.is_admin:
            return True
        if self.can_afford(amount):
            self.credits -= amount
            return True
        return False

    def add_credits(self, amount: int):
        """增加算力"""
        self.credits += amount

    def increment_processed_count(self):
        """增加处理次数计数"""
        self.total_processed += 1
        self.monthly_processed += 1
