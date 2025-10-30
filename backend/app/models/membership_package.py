from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class PackageCategory(PyEnum):
    """套餐分类"""
    MEMBERSHIP = "membership"  # 会员套餐
    DISCOUNT = "discount"      # 优惠套餐


class RefundPolicy(PyEnum):
    """退款策略"""
    REFUNDABLE = "refundable"      # 可退款
    NON_REFUNDABLE = "non_refundable"  # 不可退款


class MembershipPackage(Base):
    """会员套餐模型"""
    __tablename__ = "membership_packages"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(50), unique=True, index=True, nullable=False)

    # 套餐基本信息
    name = Column(String(100), nullable=False)  # 套餐名称
    category = Column(String(20), nullable=False)  # membership, discount
    description = Column(Text, nullable=True)  # 套餐描述

    # 价格信息
    price_yuan = Column(Integer, nullable=False)  # 价格（元）
    bonus_credits = Column(Integer, nullable=False)  # 赠送积分
    total_credits = Column(Integer, nullable=False)  # 实得积分 = price_yuan + bonus_credits

    # 退款策略
    refund_policy = Column(String(20), default=RefundPolicy.NON_REFUNDABLE.value)
    refund_deduction_rate = Column(Float, default=0.0)  # 退款扣除比例

    # 会员特权
    privileges = Column(JSON, nullable=True)  # 特权列表

    # 状态和标签
    active = Column(Boolean, default=True)
    popular = Column(Boolean, default=False)
    recommended = Column(Boolean, default=False)

    # 排序和显示
    sort_order = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MembershipPackage(id={self.id}, name={self.name}, price={self.price_yuan}元, total_credits={self.total_credits})>"

    @property
    def is_refundable(self) -> bool:
        """是否可退款"""
        return self.refund_policy == RefundPolicy.REFUNDABLE.value

    @property
    def refund_amount_yuan(self) -> float:
        """退款金额（元）"""
        if not self.is_refundable:
            return 0.0
        return self.price_yuan * (1 - self.refund_deduction_rate)

    @property
    def credits_per_yuan(self) -> float:
        """每元获得的积分"""
        if self.price_yuan == 0:
            return float('inf')
        return self.total_credits / self.price_yuan


class ServicePrice(Base):
    """服务价格模型"""
    __tablename__ = "service_prices"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String(50), unique=True, index=True, nullable=False)

    # 服务信息
    service_name = Column(String(100), nullable=False)  # 服务名称
    service_key = Column(String(50), nullable=False)  # 服务标识
    description = Column(Text, nullable=True)  # 服务描述

    # 价格信息
    price_credits = Column(Numeric(18, 2), nullable=False)  # 价格（积分）

    # 状态
    active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ServicePrice(id={self.id}, service_name={self.service_name}, price={self.price_credits}积分)>"


class UserMembership(Base):
    """用户会员记录模型"""
    __tablename__ = "user_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    package_id = Column(String(50), nullable=False, index=True)

    # 购买信息
    purchase_amount_yuan = Column(Integer, nullable=False)  # 购买金额（元）
    total_credits_received = Column(Integer, nullable=False)  # 获得的总积分

    # 会员状态
    is_active = Column(Boolean, default=True)

    # 时间信息
    purchased_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # 退款信息
    refunded_at = Column(DateTime, nullable=True)
    refund_amount_yuan = Column(Integer, default=0)  # 退款金额（元）
    refund_reason = Column(Text, nullable=True)

    # 关联订单
    order_id = Column(String(50), nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserMembership(id={self.id}, user_id={self.user_id}, package_id={self.package_id})>"

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        from datetime import datetime
        if not self.expires_at:
            return False  # 永久会员
        return datetime.utcnow() > self.expires_at

    @property
    def is_refunded(self) -> bool:
        """是否已退款"""
        return self.refunded_at is not None

    @property
    def remaining_credits(self) -> int:
        """剩余积分"""
        # 这里需要根据实际使用情况计算
        return self.total_credits_received


class NewUserBonus(Base):
    """新用户福利模型"""
    __tablename__ = "new_user_bonuses"

    id = Column(Integer, primary_key=True, index=True)

    # 福利配置
    bonus_credits = Column(Integer, default=10)  # 赠送积分
    active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NewUserBonus(id={self.id}, bonus_credits={self.bonus_credits})>"