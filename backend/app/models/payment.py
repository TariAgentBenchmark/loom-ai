from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class OrderStatus(PyEnum):
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    FAILED = "failed"  # 支付失败
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款


class PackageType(PyEnum):
    MEMBERSHIP = "membership"  # 会员套餐
    CREDITS = "credits"  # 算力充值


class PaymentMethod(PyEnum):
    ALIPAY = "alipay"  # 支付宝
    WECHAT = "wechat"  # 微信支付
    BANK_CARD = "bank_card"  # 银行卡
    PAYPAL = "paypal"  # PayPal


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 套餐信息
    package_id = Column(String(50), nullable=False)
    package_name = Column(String(100), nullable=False)
    package_type = Column(String(20), nullable=False)  # membership, credits
    
    # 价格信息
    original_amount = Column(Integer, nullable=False)  # 原价（分）
    discount_amount = Column(Integer, default=0)  # 折扣金额（分）
    final_amount = Column(Integer, nullable=False)  # 实付金额（分）
    
    # 支付信息
    payment_method = Column(String(20), nullable=False)
    payment_url = Column(String(500), nullable=True)  # 支付链接
    qr_code_url = Column(String(500), nullable=True)  # 二维码链接
    transaction_id = Column(String(100), nullable=True)  # 第三方交易ID
    
    # 订单状态
    status = Column(String(20), default=OrderStatus.PENDING.value, index=True)
    
    # 优惠券信息
    coupon_code = Column(String(50), nullable=True)
    coupon_discount = Column(Integer, default=0)  # 优惠券折扣金额
    
    # 套餐内容
    credits_amount = Column(Integer, nullable=True)  # 算力数量
    membership_duration = Column(Integer, nullable=True)  # 会员时长（天）
    
    # 发票信息
    invoice_available = Column(Boolean, default=False)
    invoice_url = Column(String(500), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)  # 订单过期时间
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 元数据
    extra_metadata = Column(JSON, nullable=True)  # 额外信息
    
    # 关联关系
    user = relationship("User", back_populates="orders")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, order_id={self.order_id}, status={self.status}, amount={self.final_amount})>"

    @property
    def is_paid(self) -> bool:
        """订单是否已支付"""
        return self.status == OrderStatus.PAID.value

    @property
    def is_expired(self) -> bool:
        """订单是否已过期"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def can_be_cancelled(self) -> bool:
        """订单是否可以取消"""
        return self.status == OrderStatus.PENDING.value and not self.is_expired

    @property
    def can_be_refunded(self) -> bool:
        """订单是否可以退款"""
        return self.status == OrderStatus.PAID.value

    def mark_as_paid(self, transaction_id: str):
        """标记订单为已支付"""
        self.status = OrderStatus.PAID.value
        self.transaction_id = transaction_id
        self.paid_at = func.now()

    def mark_as_cancelled(self):
        """标记订单为已取消"""
        self.status = OrderStatus.CANCELLED.value


class Refund(Base):
    """退款记录模型"""
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    refund_id = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 退款信息
    amount = Column(Integer, nullable=False)  # 退款金额（分）
    reason = Column(String(500), nullable=False)  # 退款原因
    description = Column(Text, nullable=True)  # 详细说明
    
    # 退款状态
    status = Column(String(20), default="processing")  # processing, approved, rejected, completed
    admin_notes = Column(Text, nullable=True)  # 管理员备注
    
    # 处理信息
    processed_by = Column(Integer, nullable=True)  # 处理人员ID
    external_refund_id = Column(String(100), nullable=True)  # 第三方退款ID
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关联关系
    order = relationship("Order", back_populates="refunds")
    user = relationship("User")

    def __repr__(self):
        return f"<Refund(id={self.id}, refund_id={self.refund_id}, amount={self.amount}, status={self.status})>"

    @property
    def is_processing(self) -> bool:
        """退款是否正在处理"""
        return self.status == "processing"

    @property
    def is_completed(self) -> bool:
        """退款是否已完成"""
        return self.status == "completed"

    def mark_as_approved(self, admin_id: int, notes: str = None):
        """标记退款为已批准"""
        self.status = "approved"
        self.processed_by = admin_id
        self.admin_notes = notes
        self.processed_at = func.now()

    def mark_as_rejected(self, admin_id: int, notes: str):
        """标记退款为已拒绝"""
        self.status = "rejected"
        self.processed_by = admin_id
        self.admin_notes = notes
        self.processed_at = func.now()

    def mark_as_completed(self, external_refund_id: str):
        """标记退款为已完成"""
        self.status = "completed"
        self.external_refund_id = external_refund_id
        self.completed_at = func.now()


class Package(Base):
    """套餐模型"""
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 套餐基本信息
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # membership, credits
    category = Column(String(20), nullable=False)  # monthly, quarterly, yearly
    
    # 价格信息
    price = Column(Integer, nullable=False)  # 价格（分）
    original_price = Column(Integer, nullable=True)  # 原价（分）
    
    # 套餐内容
    credits = Column(Integer, nullable=False)  # 算力数量
    duration = Column(Integer, nullable=True)  # 时长（天）
    
    # 特性和描述
    features = Column(JSON, nullable=True)  # 功能列表
    description = Column(Text, nullable=True)
    
    # 状态和标签
    active = Column(Boolean, default=True)
    popular = Column(Boolean, default=False)
    discount_label = Column(String(50), nullable=True)  # 折扣标签
    
    # 排序和显示
    sort_order = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Package(id={self.id}, package_id={self.package_id}, name={self.name}, price={self.price})>"

    @property
    def price_yuan(self) -> float:
        """获取人民币价格"""
        return self.price / 100.0

    @property
    def original_price_yuan(self) -> float:
        """获取原价人民币价格"""
        return (self.original_price or self.price) / 100.0

    @property
    def has_discount(self) -> bool:
        """是否有折扣"""
        return self.original_price and self.original_price > self.price


class Coupon(Base):
    """优惠券模型"""
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(String(50), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    
    # 优惠券信息
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # amount, percentage
    value = Column(Integer, nullable=False)  # 优惠值
    min_amount = Column(Integer, default=0)  # 最低消费金额
    
    # 适用范围
    applicable_packages = Column(JSON, nullable=True)  # 适用套餐ID列表
    applicable_users = Column(JSON, nullable=True)  # 适用用户ID列表（可选）
    
    # 使用限制
    max_uses = Column(Integer, nullable=True)  # 最大使用次数
    max_uses_per_user = Column(Integer, default=1)  # 每用户最大使用次数
    current_uses = Column(Integer, default=0)  # 当前使用次数
    
    # 状态
    active = Column(Boolean, default=True)
    
    # 时间限制
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Coupon(id={self.id}, code={self.code}, name={self.name}, value={self.value})>"

    @property
    def is_valid(self) -> bool:
        """优惠券是否有效"""
        from datetime import datetime
        now = datetime.utcnow()
        
        if not self.active:
            return False
        
        if self.starts_at and now < self.starts_at:
            return False
            
        if now > self.expires_at:
            return False
            
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
            
        return True

    def can_be_used_by_user(self, user_id: int, package_id: str) -> bool:
        """检查用户是否可以使用此优惠券"""
        if not self.is_valid:
            return False
            
        # 检查适用套餐
        if self.applicable_packages and package_id not in self.applicable_packages:
            return False
            
        # 检查适用用户
        if self.applicable_users and user_id not in self.applicable_users:
            return False
            
        # TODO: 检查用户使用次数限制
        
        return True

    def calculate_discount(self, amount: int) -> int:
        """计算折扣金额"""
        if self.type == "amount":
            return min(self.value, amount)
        elif self.type == "percentage":
            return int(amount * self.value / 10000)  # value是百分比*100
        return 0

    def use_coupon(self):
        """使用优惠券（增加使用次数）"""
        self.current_uses += 1
