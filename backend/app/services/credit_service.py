import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.credit import CreditTransaction, CreditTransfer, TransactionType, CreditSource
from app.services.credit_math import to_decimal, to_float


class CreditService:
    """积分服务"""

    async def record_transaction(
        self,
        db: Session,
        user_id: int,
        amount,
        source: str,
        description: str,
        related_task_id: Optional[str] = None,
        related_order_id: Optional[str] = None,
        related_transfer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CreditTransaction:
        """记录积分交易"""
        
        # 获取用户当前余额
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")
        
        normalized_amount = to_decimal(amount)
        transaction_type = TransactionType.EARN.value if normalized_amount > 0 else TransactionType.SPEND.value
        balance_after = to_decimal(user.credits or 0)

        # 创建交易记录
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type=transaction_type,
            amount=normalized_amount,
            balance_after=balance_after,
            source=source,
            description=description,
            related_task_id=related_task_id,
            related_order_id=related_order_id,
            related_transfer_id=related_transfer_id,
            details=json.dumps(metadata, ensure_ascii=False, default=str) if metadata else None
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction

    async def get_user_balance(self, db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户积分余额信息"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")
        
        current_balance = to_decimal(user.credits or 0)

        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_spent_raw = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.type == TransactionType.SPEND.value,
                CreditTransaction.created_at >= current_month_start
            )
        ).scalar()
        monthly_spent = to_decimal(monthly_spent_raw or 0).copy_abs()

        monthly_quotas = {
            "free": Decimal("200"),
            "basic": Decimal("7500"),
            "premium": Decimal("11000"),
            "enterprise": Decimal("30000"),
        }

        membership_key = user.membership_type.value if user.membership_type else "free"
        monthly_quota = monthly_quotas.get(membership_key, Decimal("200"))
        monthly_remaining = monthly_quota - monthly_spent
        if monthly_remaining < 0:
            monthly_remaining = Decimal("0")

        usage_percent = float((monthly_spent / monthly_quota * 100) if monthly_quota > 0 else 0.0)

        earned_sum = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.type == TransactionType.EARN.value
            )
        ).scalar()
        total_earned = to_decimal(earned_sum or 0)

        spent_sum = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.type == TransactionType.SPEND.value
            )
        ).scalar()
        total_spent = to_decimal(spent_sum or 0).copy_abs()
        net_change = total_earned - total_spent
        
        return {
            "credits": to_float(current_balance),
            "totalEarned": to_float(total_earned),
            "totalSpent": to_float(total_spent),
            "netChange": to_float(net_change),
            "monthlySpent": to_float(monthly_spent),
            "monthlyQuota": float(monthly_quota),
            "monthlyRemaining": to_float(monthly_remaining),
            "monthlyUsagePercent": round(usage_percent, 1),
            "lastUpdated": now.isoformat()
        }

    async def get_transaction_history(
        self,
        db: Session,
        user_id: int,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取交易历史"""
        
        query = db.query(CreditTransaction).filter(CreditTransaction.user_id == user_id)
        
        if transaction_type:
            query = query.filter(CreditTransaction.type == transaction_type)
        
        if start_date:
            query = query.filter(CreditTransaction.created_at >= start_date)
        
        if end_date:
            query = query.filter(CreditTransaction.created_at <= end_date)
        
        # 按时间倒序排列
        query = query.order_by(CreditTransaction.created_at.desc())
        
        # 分页
        total = query.count()
        transactions = query.offset((page - 1) * limit).limit(limit).all()
        
        # 计算统计信息
        total_earned_raw = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.type == TransactionType.EARN.value,
                CreditTransaction.created_at >= (start_date or datetime(1970, 1, 1)),
                CreditTransaction.created_at <= (end_date or datetime.utcnow())
            )
        ).scalar()
        total_earned = to_decimal(total_earned_raw or 0)
        
        total_spent_raw = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.type == TransactionType.SPEND.value,
                CreditTransaction.created_at >= (start_date or datetime(1970, 1, 1)),
                CreditTransaction.created_at <= (end_date or datetime.utcnow())
            )
        ).scalar()
        total_spent = to_decimal(total_spent_raw or 0).copy_abs()
        
        return {
            "transactions": transactions,
            "summary": {
                "totalEarned": to_float(total_earned),
                "totalSpent": to_float(total_spent),
                "netChange": to_float(total_earned - total_spent),
                "period": f"{start_date.strftime('%Y-%m-%d') if start_date else '开始'} to {end_date.strftime('%Y-%m-%d') if end_date else '现在'}"
            },
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }

    async def transfer_credits(
        self,
        db: Session,
        sender_id: int,
        recipient_email: str,
        amount,
        message: Optional[str] = None
    ) -> CreditTransfer:
        """转赠积分"""
        
        # 获取发送方用户
        sender = db.query(User).filter(User.id == sender_id).first()
        if not sender:
            raise Exception("发送方用户不存在")
        
        # 获取接收方用户
        recipient = db.query(User).filter(User.email == recipient_email).first()
        if not recipient:
            raise Exception("接收方用户不存在")
        
        if sender.id == recipient.id:
            raise Exception("不能向自己转赠积分")

        normalized_amount = to_decimal(amount)
        
        # 检查发送方余额（管理员用户有无限积分）
        if not sender.can_afford(normalized_amount):
            raise Exception("积分余额不足")
        
        # 执行转账（管理员用户不需要扣除积分）
        sender.deduct_credits(normalized_amount)
        recipient.add_credits(normalized_amount)
        
        # 创建转赠记录
        transfer = CreditTransfer(
            transfer_id=f"transfer_{uuid.uuid4().hex[:12]}",
            sender_id=sender.id,
            recipient_id=recipient.id,
            amount=normalized_amount,
            message=message,
            status="completed"
        )
        
        db.add(transfer)
        
        # 记录双方的积分交易
        await self.record_transaction(
            db=db,
            user_id=sender.id,
            amount=-normalized_amount,
            source=CreditSource.TRANSFER_OUT.value,
            description=f"转赠积分给 {recipient_email}",
            related_transfer_id=transfer.transfer_id
        )
        
        await self.record_transaction(
            db=db,
            user_id=recipient.id,
            amount=normalized_amount,
            source=CreditSource.TRANSFER_IN.value,
            description=f"收到来自 {sender.email} 的积分转赠",
            related_transfer_id=transfer.transfer_id
        )
        
        db.commit()
        db.refresh(transfer)
        
        return transfer

    async def get_transfer_history(
        self,
        db: Session,
        user_id: int,
        transfer_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取转赠历史"""
        
        if transfer_type == "sent":
            query = db.query(CreditTransfer).filter(CreditTransfer.sender_id == user_id)
        elif transfer_type == "received":
            query = db.query(CreditTransfer).filter(CreditTransfer.recipient_id == user_id)
        else:
            query = db.query(CreditTransfer).filter(
                or_(
                    CreditTransfer.sender_id == user_id,
                    CreditTransfer.recipient_id == user_id
                )
            )
        
        # 按时间倒序
        query = query.order_by(CreditTransfer.created_at.desc())
        
        # 分页
        total = query.count()
        transfers = query.offset((page - 1) * limit).limit(limit).all()
        
        return {
            "transfers": transfers,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }

    async def get_credit_statistics(
        self,
        db: Session,
        user_id: int,
        period: str = "daily"
    ) -> Dict[str, Any]:
        """获取积分统计"""
        
        # 计算时间范围
        now = datetime.utcnow()
        if period == "daily":
            start_date = now - timedelta(days=30)
            date_format = "%Y-%m-%d"
        elif period == "weekly":
            start_date = now - timedelta(weeks=12)
            date_format = "%Y-W%U"
        elif period == "monthly":
            start_date = now - timedelta(days=365)
            date_format = "%Y-%m"
        else:
            start_date = now - timedelta(days=365)
            date_format = "%Y"
        
        # 查询交易记录
        transactions = db.query(CreditTransaction).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.created_at >= start_date
            )
        ).order_by(CreditTransaction.created_at.asc()).all()
        
        # 按日期分组统计
        stats_dict = {}
        for txn in transactions:
            date_key = txn.created_at.strftime(date_format)
            
            if date_key not in stats_dict:
                stats_dict[date_key] = {
                    "date": date_key,
                    "earned": Decimal("0"),
                    "spent": Decimal("0"),
                    "balance": Decimal("0"),
                    "tasks": 0
                }
            
            if txn.type == TransactionType.EARN.value:
                stats_dict[date_key]["earned"] += to_decimal(txn.amount)
            else:
                stats_dict[date_key]["spent"] += to_decimal(txn.amount).copy_abs()
                if txn.source == "processing":
                    stats_dict[date_key]["tasks"] += 1
            
            stats_dict[date_key]["balance"] = to_decimal(txn.balance_after)

        statistics = []
        for stat in stats_dict.values():
            statistics.append({
                "date": stat["date"],
                "earned": to_float(stat["earned"]),
                "spent": to_float(stat["spent"]),
                "balance": to_float(stat["balance"]),
                "tasks": stat["tasks"]
            })
        
        # 计算总计
        total_earned = sum(to_decimal(stat["earned"]) for stat in statistics)
        total_spent = sum(to_decimal(stat["spent"]) for stat in statistics)
        total_tasks = sum(stat["tasks"] for stat in statistics)
        avg_daily = (total_spent / len(statistics)) if statistics else Decimal("0")
        
        return {
            "period": period,
            "statistics": statistics,
            "summary": {
                "totalEarned": to_float(total_earned),
                "totalSpent": to_float(total_spent),
                "averageDaily": float(round(avg_daily, 1)) if statistics else 0,
                "totalTasks": total_tasks,
                "period": f"最近{len(statistics)}{'天' if period == 'daily' else '周' if period == 'weekly' else '月'}"
            }
        }

    async def check_low_balance_alert(self, db: Session, user: User) -> bool:
        """检查低余额预警"""
        if to_decimal(user.credits or 0) < to_decimal(10):
            return True
        return False

    async def add_credits_from_purchase(
        self,
        db: Session,
        user_id: int,
        amount,
        order_id: str,
        package_name: str
    ) -> CreditTransaction:
        """购买套餐后增加积分"""
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")
        
        normalized_amount = to_decimal(amount)
        user.add_credits(normalized_amount)
        
        transaction = await self.record_transaction(
            db=db,
            user_id=user_id,
            amount=normalized_amount,
            source=CreditSource.PURCHASE.value,
            description=f"{package_name}购买",
            related_order_id=order_id
        )
        
        db.commit()
        return transaction
