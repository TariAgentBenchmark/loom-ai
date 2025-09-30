from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class TransactionType(PyEnum):
    EARN = "earn"  # 获得算力
    SPEND = "spend"  # 消耗算力


class CreditSource(PyEnum):
    REGISTRATION = "registration"  # 注册赠送
    PURCHASE = "purchase"  # 购买套餐
    RECHARGE = "recharge"  # 算力充值
    TRANSFER_IN = "transfer_in"  # 转入
    TRANSFER_OUT = "transfer_out"  # 转出
    PROCESSING = "processing"  # 图片处理消耗
    REFUND = "refund"  # 退款
    ADMIN_ADJUST = "admin_adjust"  # 管理员调整


class CreditTransaction(Base):
    """算力交易记录模型"""
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 交易信息
    type = Column(String(20), nullable=False, index=True)  # earn, spend
    amount = Column(Integer, nullable=False)  # 算力变动量（正数为获得，负数为消耗）
    balance_after = Column(Integer, nullable=False)  # 交易后余额
    
    # 来源和描述
    source = Column(String(50), nullable=False, index=True)  # 来源类型
    description = Column(String(500), nullable=False)  # 交易描述
    
    # 关联信息
    related_task_id = Column(String(50), nullable=True)  # 关联任务ID
    related_order_id = Column(String(50), nullable=True)  # 关联订单ID
    related_transfer_id = Column(String(50), nullable=True)  # 关联转账ID
    
    # 元数据
    details = Column(Text, nullable=True)  # JSON格式的额外信息
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="credit_transactions")

    def __repr__(self):
        return f"<CreditTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.type})>"


class CreditTransfer(Base):
    """算力转赠记录模型"""
    __tablename__ = "credit_transfers"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # 转账双方
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 转账信息
    amount = Column(Integer, nullable=False)  # 转赠数量
    message = Column(String(500), nullable=True)  # 转赠留言
    status = Column(String(20), default="completed")  # completed, failed
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])

    def __repr__(self):
        return f"<CreditTransfer(id={self.id}, sender_id={self.sender_id}, recipient_id={self.recipient_id}, amount={self.amount})>"


class CreditAlert(Base):
    """算力预警设置模型"""
    __tablename__ = "credit_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # 预警设置
    low_balance_enabled = Column(Boolean, default=True)
    low_balance_threshold = Column(Integer, default=200)
    low_balance_methods = Column(String(100), default="email,push")  # 通知方式
    
    monthly_usage_enabled = Column(Boolean, default=True)
    monthly_usage_threshold = Column(Float, default=0.8)  # 80%
    monthly_usage_methods = Column(String(100), default="email")
    
    membership_expiry_enabled = Column(Boolean, default=True)
    membership_expiry_days = Column(Integer, default=7)  # 提前7天
    membership_expiry_methods = Column(String(100), default="email,sms")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User")

    def __repr__(self):
        return f"<CreditAlert(id={self.id}, user_id={self.user_id})>"
