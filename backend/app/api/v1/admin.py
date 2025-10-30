import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, condecimal
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, CreditSource, TransactionType, CreditTransfer, CreditAlert
from app.models.payment import Order, Refund, OrderStatus, PackageType, PaymentMethod, Package
from app.models.task import Task
from app.api.dependencies import get_current_active_admin
from app.api.decorators import admin_required, admin_route
from app.schemas.common import SuccessResponse, PaginationMeta
from app.services.auth_service import AuthService
from app.services.credit_math import to_decimal, to_float

router = APIRouter()

CreditBalance = condecimal(max_digits=12, decimal_places=2, ge=0, le=1_000_000)
CreditDelta = condecimal(max_digits=12, decimal_places=2)


class AdminUserResponse(BaseModel):
    userId: str
    email: Optional[str]
    nickname: Optional[str]
    credits: float
    membershipType: str
    status: str
    isAdmin: bool
    createdAt: str
    lastLoginAt: Optional[str]


class AdminUserListResponse(BaseModel):
    users: List[AdminUserResponse]
    pagination: PaginationMeta


class AdminCreateUserRequest(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20, description="User phone number")
    password: str = Field(..., min_length=6, max_length=128, description="Initial login password")
    email: Optional[EmailStr] = Field(None, description="User email address")
    nickname: Optional[str] = Field(None, max_length=100, description="Display nickname")
    initialCredits: CreditBalance = Field(Decimal("0.00"), description="Initial credit balance")
    isAdmin: bool = Field(False, description="Whether the user should have admin permissions")


class AdminDeleteUserRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deleting the user")


# Subscription Management Models
class UserSubscriptionUpdate(BaseModel):
    membershipType: str = Field(..., description="New membership type")
    duration: Optional[int] = Field(None, description="Duration in days, None for lifetime")
    reason: str = Field(..., description="Reason for subscription change")


class UserSubscriptionResponse(BaseModel):
    userId: str
    email: str
    currentMembership: str
    newMembership: str
    membershipExpiry: Optional[str]
    changedBy: str
    changedAt: str
    reason: str


# Credit Transaction Models
class AdminCreditTransactionResponse(BaseModel):
    transactionId: str
    userId: str
    userEmail: str
    type: str
    amount: float
    balanceAfter: float
    source: str
    description: str
    createdAt: str
    relatedTaskId: Optional[str]
    relatedOrderId: Optional[str]


class AdminCreditTransactionListResponse(BaseModel):
    transactions: List[AdminCreditTransactionResponse]
    pagination: PaginationMeta
    summary: Dict[str, Any]


class CreditAdjustmentRequest(BaseModel):
    amount: CreditDelta = Field(..., description="Amount to adjust (positive to add, negative to deduct)")
    reason: str = Field(..., description="Reason for adjustment")
    sendNotification: bool = Field(True, description="Send notification to user")


# Order Management Models
class AdminOrderResponse(BaseModel):
    orderId: str
    userId: str
    userEmail: str
    packageId: str
    packageName: str
    packageType: str
    originalAmount: int
    discountAmount: int
    finalAmount: int
    paymentMethod: str
    status: str
    createdAt: str
    paidAt: Optional[str]
    expiresAt: str
    creditsAmount: Optional[int]
    membershipDuration: Optional[int]


class AdminOrderListResponse(BaseModel):
    orders: List[AdminOrderResponse]
    pagination: PaginationMeta
    summary: Dict[str, Any]


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="New order status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    adminNotes: Optional[str] = Field(None, description="Admin notes")


# Refund Management Models
class AdminRefundResponse(BaseModel):
    refundId: str
    orderId: str
    userId: str
    userEmail: str
    amount: int
    reason: str
    status: str
    createdAt: str
    processedAt: Optional[str]
    completedAt: Optional[str]
    processedBy: Optional[str]
    adminNotes: Optional[str]


class AdminRefundListResponse(BaseModel):
    refunds: List[AdminRefundResponse]
    pagination: PaginationMeta
    summary: Dict[str, Any]


class RefundActionRequest(BaseModel):
    action: str = Field(..., description="Action: approve, reject, complete")
    reason: Optional[str] = Field(None, description="Reason for action")
    adminNotes: Optional[str] = Field(None, description="Admin notes")
    externalRefundId: Optional[str] = Field(None, description="External refund ID for completion")


# Audit Log Models
class AdminAuditLog(BaseModel):
    adminId: str
    adminEmail: str
    action: str
    targetType: str
    targetId: str
    details: Dict[str, Any]
    timestamp: str
    ipAddress: Optional[str]
    userAgent: Optional[str]


class AdminAuditLogResponse(BaseModel):
    logs: List[AdminAuditLog]
    pagination: PaginationMeta


# Enhanced Dashboard Stats
class AdminDashboardStats(BaseModel):
    users: Dict[str, Any]
    credits: Dict[str, Any]
    orders: Dict[str, Any]
    revenue: Dict[str, Any]
    subscriptions: Dict[str, Any]
    recentActivity: List[Dict[str, Any]]


@router.get("/users", dependencies=[Depends(admin_route())])
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by user status"),
    membership_filter: Optional[str] = Query(None, description="Filter by membership type"),
    email_filter: Optional[str] = Query(None, description="Filter by email (contains)"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取所有用户列表（管理员专用）"""
    try:
        query = db.query(User)
        
        # 应用过滤器
        if status_filter:
            try:
                status_enum = UserStatus(status_filter)
                query = query.filter(User.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的状态过滤器")
        
        if membership_filter:
            try:
                membership_enum = MembershipType(membership_filter)
                query = query.filter(User.membership_type == membership_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的会员类型过滤器")
        
        if email_filter:
            query = query.filter(User.email.ilike(f"%{email_filter}%"))
        
        # 应用排序
        if hasattr(User, sort_by):
            order_column = getattr(User, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
        
        # 计算总数
        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        
        # 分页
        offset = (page - 1) * page_size
        users = query.offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        user_list = []
        for user in users:
            user_list.append(AdminUserResponse(
                userId=user.user_id,
                email=user.email,
                nickname=user.nickname,
                credits=to_float(user.credits),
                membershipType=user.membership_type.value,
                status=user.status.value,
                isAdmin=user.is_admin,
                createdAt=user.created_at.isoformat() if user.created_at else "",
                lastLoginAt=user.last_login_at.isoformat() if user.last_login_at else None
            ))
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_users_list",
            target_type="users",
            target_id="list",
            details={
                "page": page,
                "page_size": page_size,
                "filters": {
                    "status": status_filter,
                    "membership": membership_filter,
                    "email": email_filter
                },
                "total_results": total
            }
        )
        
        return SuccessResponse(
            data=AdminUserListResponse(
                users=user_list,
                pagination=PaginationMeta(
                    page=page,
                    limit=page_size,
                    total=total,
                    total_pages=total_pages
                ).dict()
            ).dict(),
            message="获取用户列表成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", dependencies=[Depends(admin_route())])
async def get_user_detail(
    user_id: str,
    db: Session = Depends(get_db)
):
    """获取特定用户详情（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        user_detail = AdminUserResponse(
            userId=user.user_id,
            email=user.email,
            nickname=user.nickname,
            credits=to_float(user.credits),
            membershipType=user.membership_type.value,
            status=user.status.value,
            isAdmin=user.is_admin,
            createdAt=user.created_at.isoformat() if user.created_at else "",
            lastLoginAt=user.last_login_at.isoformat() if user.last_login_at else None
        )
        
        return SuccessResponse(
            data=user_detail.dict(),
            message="获取用户详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", dependencies=[Depends(admin_route())])
async def create_user(
    user_data: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """创建新用户（管理员专用）"""
    auth_service = AuthService()

    try:
        # 检查手机号是否存在
        existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="手机号已存在")

        # 检查邮箱是否存在
        if user_data.email:
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已存在")

        user = User(
            user_id=f"user_{uuid.uuid4().hex[:12]}",
            phone=user_data.phone,
            email=user_data.email,
            nickname=user_data.nickname or user_data.phone,
            hashed_password=auth_service.get_password_hash(user_data.password),
            credits=to_decimal(user_data.initialCredits),
            membership_type=MembershipType.FREE,
            status=UserStatus.ACTIVE,
            is_admin=user_data.isAdmin
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        initial_credits = to_decimal(user_data.initialCredits)

        if initial_credits > to_decimal(0):
            from app.services.credit_service import CreditService
            credit_service = CreditService()
            await credit_service.record_transaction(
                db=db,
                user_id=user.id,
                amount=initial_credits,
                source=CreditSource.ADMIN_ADJUST.value,
                description="管理员创建用户赠送积分"
            )

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="create_user",
            target_type="user",
            target_id=user.user_id,
            details={
                "phone": user.phone,
                "email": user.email,
                "initialCredits": to_float(initial_credits),
                "isAdmin": user_data.isAdmin
            }
        )

        return SuccessResponse(
            data=AdminUserResponse(
                userId=user.user_id,
                email=user.email,
                nickname=user.nickname,
                credits=to_float(user.credits),
                membershipType=user.membership_type.value,
                status=user.status.value,
                isAdmin=user.is_admin,
                createdAt=user.created_at.isoformat() if user.created_at else "",
                lastLoginAt=user.last_login_at.isoformat() if user.last_login_at else None
            ).dict(),
            message="用户创建成功"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class UserStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


@router.put("/users/{user_id}/status", dependencies=[Depends(admin_route())])
async def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db)
):
    """更新用户状态（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 验证状态值
        try:
            new_status = UserStatus(status_update.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值")
        
        # 更新状态
        user.status = new_status
        db.commit()
        
        return SuccessResponse(
            data={
                "userId": user.user_id,
                "status": user.status.value,
                "reason": status_update.reason
            },
            message=f"用户状态已更新为: {new_status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", dependencies=[Depends(admin_route())])
async def delete_user(
    user_id: str,
    delete_request: Optional[AdminDeleteUserRequest] = Body(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """删除用户（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user.is_admin:
            raise HTTPException(status_code=400, detail="无法删除管理员账户")

        if user.id == current_admin.id:
            raise HTTPException(status_code=400, detail="无法删除当前登录的管理员")

        # 删除积分相关记录
        db.query(CreditTransaction).filter(CreditTransaction.user_id == user.id).delete(synchronize_session=False)
        db.query(CreditAlert).filter(CreditAlert.user_id == user.id).delete(synchronize_session=False)
        db.query(CreditTransfer).filter(
            or_(CreditTransfer.sender_id == user.id, CreditTransfer.recipient_id == user.id)
        ).delete(synchronize_session=False)

        # 删除退款记录需在订单之前
        db.query(Refund).filter(Refund.user_id == user.id).delete(synchronize_session=False)

        # 删除订单（包含退款关系）
        orders = db.query(Order).filter(Order.user_id == user.id).all()
        for order in orders:
            db.delete(order)

        # 删除任务（包含任务分享）
        tasks = db.query(Task).filter(Task.user_id == user.id).all()
        for task in tasks:
            db.delete(task)

        # 最后删除用户
        db.delete(user)
        db.commit()

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="delete_user",
            target_type="user",
            target_id=user_id,
            details={
                "reason": delete_request.reason if delete_request else None
            }
        )

        return SuccessResponse(
            data={
                "userId": user_id,
                "deletedAt": datetime.utcnow().isoformat()
            },
            message="用户已删除"
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class UserCreditsUpdate(BaseModel):
    credits: CreditBalance
    reason: str


@router.put("/users/{user_id}/credits", dependencies=[Depends(admin_route())])
async def update_user_credits(
    user_id: str,
    credits_update: UserCreditsUpdate,
    db: Session = Depends(get_db)
):
    """更新用户积分（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_credits = to_decimal(user.credits or 0)
        new_credits = to_decimal(credits_update.credits)
        user.credits = new_credits
        db.commit()
        
        # 记录积分变更
        from app.services.credit_service import CreditService
        credit_service = CreditService()
        await credit_service.record_transaction(
            db=db,
            user_id=user.id,
            amount=new_credits - old_credits,
            source="admin_adjustment",
            description=f"管理员调整: {credits_update.reason}"
        )
        
        return SuccessResponse(
            data={
                "userId": user.user_id,
                "oldCredits": to_float(old_credits),
                "newCredits": to_float(new_credits),
                "reason": credits_update.reason
            },
            message="用户积分已更新"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Audit logging helper function
async def log_admin_action(
    db: Session,
    admin: User,
    action: str,
    target_type: str,
    target_id: str,
    details: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """记录管理员操作日志"""
    try:
        # 这里可以创建一个专门的审计日志表，暂时记录在系统日志中
        import logging
        logger = logging.getLogger(__name__)
        
        audit_log = {
            "adminId": admin.user_id,
            "adminEmail": admin.email,
            "action": action,
            "targetType": target_type,
            "targetId": target_id,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "ipAddress": ip_address,
            "userAgent": user_agent
        }
        
        logger.info(f"Admin action: {audit_log}")
    except Exception as e:
        # 记录日志失败不应该影响主要功能
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log admin action: {str(e)}")


# Subscription Management Endpoints
@router.put("/users/{user_id}/subscription", dependencies=[Depends(admin_route())])
async def update_user_subscription(
    user_id: str,
    subscription_update: UserSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """更新用户订阅（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 验证会员类型
        try:
            new_membership = MembershipType(subscription_update.membershipType)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的会员类型")
        
        old_membership = user.membership_type
        old_expiry = user.membership_expiry
        
        # 更新会员信息
        user.membership_type = new_membership
        if subscription_update.duration:
            user.membership_expiry = datetime.utcnow() + timedelta(days=subscription_update.duration)
        elif new_membership == MembershipType.FREE:
            user.membership_expiry = None
        
        db.commit()
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="update_subscription",
            target_type="user",
            target_id=user_id,
            details={
                "oldMembership": old_membership.value,
                "newMembership": new_membership.value,
                "oldExpiry": old_expiry.isoformat() if old_expiry else None,
                "newExpiry": user.membership_expiry.isoformat() if user.membership_expiry else None,
                "duration": subscription_update.duration,
                "reason": subscription_update.reason
            }
        )
        
        return SuccessResponse(
            data=UserSubscriptionResponse(
                userId=user.user_id,
                email=user.email,
                currentMembership=old_membership.value,
                newMembership=new_membership.value,
                membershipExpiry=user.membership_expiry.isoformat() if user.membership_expiry else None,
                changedBy=current_admin.email,
                changedAt=datetime.utcnow().isoformat(),
                reason=subscription_update.reason
            ).dict(),
            message="用户订阅已更新"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Credit Transaction Management Endpoints
@router.get("/users/{user_id}/transactions", dependencies=[Depends(admin_route())])
async def get_user_credit_transactions(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    source_filter: Optional[str] = Query(None, description="Filter by transaction source"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取用户积分交易记录（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        query = db.query(CreditTransaction).filter(CreditTransaction.user_id == user.id)
        
        # 应用过滤器
        if transaction_type:
            query = query.filter(CreditTransaction.type == transaction_type)
        
        if source_filter:
            query = query.filter(CreditTransaction.source == source_filter)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(CreditTransaction.created_at >= start)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的开始日期格式")
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(CreditTransaction.created_at < end)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的结束日期格式")
        
        # 按时间倒序排列
        query = query.order_by(desc(CreditTransaction.created_at))
        
        # 分页
        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        transactions = query.offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        transaction_list = []
        for txn in transactions:
            transaction_list.append(AdminCreditTransactionResponse(
                transactionId=txn.transaction_id,
                userId=user.user_id,
                userEmail=user.email,
                type=txn.type,
                amount=to_float(txn.amount),
                balanceAfter=to_float(txn.balance_after),
                source=txn.source,
                description=txn.description,
                createdAt=txn.created_at.isoformat(),
                relatedTaskId=txn.related_task_id,
                relatedOrderId=txn.related_order_id
            ))
        
        # 计算统计信息
        total_earned_raw = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user.id,
                CreditTransaction.type == TransactionType.EARN.value
            )
        ).scalar()
        
        total_spent_raw = db.query(func.sum(CreditTransaction.amount)).filter(
            and_(
                CreditTransaction.user_id == user.id,
                CreditTransaction.type == TransactionType.SPEND.value
            )
        ).scalar()

        total_earned = to_decimal(total_earned_raw or 0)
        total_spent = to_decimal(total_spent_raw or 0).copy_abs()
        net_change = total_earned - total_spent
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_user_transactions",
            target_type="user",
            target_id=user_id,
            details={
                "page": page,
                "page_size": page_size,
                "filters": {
                    "type": transaction_type,
                    "source": source_filter,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": total
            }
        )
        
        return SuccessResponse(
            data=AdminCreditTransactionListResponse(
                transactions=transaction_list,
                pagination=PaginationMeta(
                    page=page,
                    limit=page_size,
                    total=total,
                    total_pages=total_pages
                ).dict(),
                summary={
                    "totalEarned": to_float(total_earned),
                    "totalSpent": to_float(total_spent),
                    "netChange": to_float(net_change),
                    "currentBalance": to_float(user.credits)
                }
            ).dict(),
            message="获取用户交易记录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/credits/adjust", dependencies=[Depends(admin_route())])
async def adjust_user_credits(
    user_id: str,
    adjustment: CreditAdjustmentRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """调整用户积分（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_credits = to_decimal(user.credits or 0)
        delta = to_decimal(adjustment.amount)
        user.credits = old_credits + delta
        db.commit()
        
        # 记录积分变更
        from app.services.credit_service import CreditService
        credit_service = CreditService()
        await credit_service.record_transaction(
            db=db,
            user_id=user.id,
            amount=delta,
            source=CreditSource.ADMIN_ADJUST.value,
            description=f"管理员调整: {adjustment.reason}"
        )
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="adjust_credits",
            target_type="user",
            target_id=user_id,
            details={
                "oldCredits": to_float(old_credits),
                "newCredits": to_float(user.credits),
                "adjustment": to_float(delta),
                "reason": adjustment.reason,
                "sendNotification": adjustment.sendNotification
            }
        )
        
        # TODO: 发送通知给用户
        
        return SuccessResponse(
            data={
                "userId": user.user_id,
                "oldCredits": to_float(old_credits),
                "newCredits": to_float(user.credits),
                "adjustment": to_float(delta),
                "reason": adjustment.reason
            },
            message="用户积分已调整"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Order Management Endpoints
@router.get("/orders", dependencies=[Depends(admin_route())])
async def get_all_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    user_filter: Optional[str] = Query(None, description="Filter by user email or ID"),
    package_type_filter: Optional[str] = Query(None, description="Filter by package type"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取所有订单列表（管理员专用）"""
    try:
        query = db.query(Order).join(User, Order.user_id == User.id)
        
        # 应用过滤器
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        if user_filter:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{user_filter}%"),
                    User.user_id.ilike(f"%{user_filter}%")
                )
            )
        
        if package_type_filter:
            query = query.filter(Order.package_type == package_type_filter)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(Order.created_at >= start)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的开始日期格式")
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Order.created_at < end)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的结束日期格式")
        
        # 按创建时间倒序排列
        query = query.order_by(desc(Order.created_at))
        
        # 分页
        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        orders = query.offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        order_list = []
        for order in orders:
            order_list.append(AdminOrderResponse(
                orderId=order.order_id,
                userId=order.user.user_id,
                userEmail=order.user.email,
                packageId=order.package_id,
                packageName=order.package_name,
                packageType=order.package_type,
                originalAmount=order.original_amount,
                discountAmount=order.discount_amount,
                finalAmount=order.final_amount,
                paymentMethod=order.payment_method,
                status=order.status,
                createdAt=order.created_at.isoformat(),
                paidAt=order.paid_at.isoformat() if order.paid_at else None,
                expiresAt=order.expires_at.isoformat(),
                creditsAmount=order.credits_amount,
                membershipDuration=order.membership_duration
            ))
        
        # 计算统计信息
        total_revenue = db.query(func.sum(Order.final_amount)).filter(
            Order.status == OrderStatus.PAID.value
        ).scalar() or 0
        
        pending_orders = db.query(Order).filter(
            Order.status == OrderStatus.PENDING.value
        ).count()
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_orders_list",
            target_type="orders",
            target_id="list",
            details={
                "page": page,
                "page_size": page_size,
                "filters": {
                    "status": status_filter,
                    "user": user_filter,
                    "package_type": package_type_filter,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": total
            }
        )
        
        return SuccessResponse(
            data=AdminOrderListResponse(
                orders=order_list,
                pagination=PaginationMeta(
                    page=page,
                    limit=page_size,
                    total=total,
                    total_pages=total_pages
                ).dict(),
                summary={
                    "totalRevenue": total_revenue,
                    "pendingOrders": pending_orders,
                    "conversionRate": round((total - pending_orders) / total * 100, 2) if total > 0 else 0
                }
            ).dict(),
            message="获取订单列表成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", dependencies=[Depends(admin_route())])
async def get_order_detail(
    order_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取订单详情（管理员专用）"""
    try:
        order = db.query(Order).join(User, Order.user_id == User.id).filter(
            Order.order_id == order_id
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        order_detail = AdminOrderResponse(
            orderId=order.order_id,
            userId=order.user.user_id,
            userEmail=order.user.email,
            packageId=order.package_id,
            packageName=order.package_name,
            packageType=order.package_type,
            originalAmount=order.original_amount,
            discountAmount=order.discount_amount,
            finalAmount=order.final_amount,
            paymentMethod=order.payment_method,
            status=order.status,
            createdAt=order.created_at.isoformat(),
            paidAt=order.paid_at.isoformat() if order.paid_at else None,
            expiresAt=order.expires_at.isoformat(),
            creditsAmount=order.credits_amount,
            membershipDuration=order.membership_duration
        )
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_order_detail",
            target_type="order",
            target_id=order_id,
            details={}
        )
        
        return SuccessResponse(
            data=order_detail.dict(),
            message="获取订单详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}/status", dependencies=[Depends(admin_route())])
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """更新订单状态（管理员专用）"""
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        
        # 验证状态值
        valid_statuses = [status.value for status in OrderStatus]
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail="无效的订单状态")
        
        old_status = order.status
        order.status = status_update.status
        
        # 如果标记为已支付，记录支付时间
        if status_update.status == OrderStatus.PAID.value and old_status != OrderStatus.PAID.value:
            order.paid_at = datetime.utcnow()
            
            # 如果是套餐订单，需要添加相应的积分或延长会员
            if order.package_type == PackageType.CREDITS.value and order.credits_amount:
                user = db.query(User).filter(User.id == order.user_id).first()
                if user:
                    user.add_credits(order.credits_amount)
                    
                    # 记录积分交易
                    from app.services.credit_service import CreditService
                    credit_service = CreditService()
                    await credit_service.add_credits_from_purchase(
                        db=db,
                        user_id=user.id,
                        amount=order.credits_amount,
                        order_id=order.order_id,
                        package_name=order.package_name
                    )
            
            elif order.package_type == PackageType.MEMBERSHIP.value and order.membership_duration:
                user = db.query(User).filter(User.id == order.user_id).first()
                if user:
                    # 延长会员期限
                    if user.membership_expiry and user.membership_expiry > datetime.utcnow():
                        user.membership_expiry = user.membership_expiry + timedelta(days=order.membership_duration)
                    else:
                        user.membership_expiry = datetime.utcnow() + timedelta(days=order.membership_duration)
        
        db.commit()
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="update_order_status",
            target_type="order",
            target_id=order_id,
            details={
                "oldStatus": old_status,
                "newStatus": status_update.status,
                "reason": status_update.reason,
                "adminNotes": status_update.adminNotes
            }
        )
        
        return SuccessResponse(
            data={
                "orderId": order.order_id,
                "oldStatus": old_status,
                "newStatus": order.status,
                "reason": status_update.reason,
                "adminNotes": status_update.adminNotes
            },
            message="订单状态已更新"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Refund Management Endpoints
@router.get("/refunds", dependencies=[Depends(admin_route())])
async def get_all_refunds(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by refund status"),
    user_filter: Optional[str] = Query(None, description="Filter by user email or ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取所有退款申请列表（管理员专用）"""
    try:
        query = db.query(Refund).join(User, Refund.user_id == User.id).join(Order, Refund.order_id == Order.id)
        
        # 应用过滤器
        if status_filter:
            query = query.filter(Refund.status == status_filter)
        
        if user_filter:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{user_filter}%"),
                    User.user_id.ilike(f"%{user_filter}%")
                )
            )
        
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(Refund.created_at >= start)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的开始日期格式")
        
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(Refund.created_at < end)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的结束日期格式")
        
        # 按创建时间倒序排列
        query = query.order_by(desc(Refund.created_at))
        
        # 分页
        total = query.count()
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        refunds = query.offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        refund_list = []
        for refund in refunds:
            processed_by_email = None
            if refund.processed_by:
                processed_by_user = db.query(User).filter(User.id == refund.processed_by).first()
                if processed_by_user:
                    processed_by_email = processed_by_user.email
            
            refund_list.append(AdminRefundResponse(
                refundId=refund.refund_id,
                orderId=refund.order.order_id,
                userId=refund.user.user_id,
                userEmail=refund.user.email,
                amount=refund.amount,
                reason=refund.reason,
                status=refund.status,
                createdAt=refund.created_at.isoformat(),
                processedAt=refund.processed_at.isoformat() if refund.processed_at else None,
                completedAt=refund.completed_at.isoformat() if refund.completed_at else None,
                processedBy=processed_by_email,
                adminNotes=refund.admin_notes
            ))
        
        # 计算统计信息
        pending_refunds = db.query(Refund).filter(Refund.status == "processing").count()
        approved_refunds = db.query(Refund).filter(Refund.status == "approved").count()
        total_refund_amount = db.query(func.sum(Refund.amount)).filter(
            Refund.status == "completed"
        ).scalar() or 0
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_refunds_list",
            target_type="refunds",
            target_id="list",
            details={
                "page": page,
                "page_size": page_size,
                "filters": {
                    "status": status_filter,
                    "user": user_filter,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "total_results": total
            }
        )
        
        return SuccessResponse(
            data=AdminRefundListResponse(
                refunds=refund_list,
                pagination=PaginationMeta(
                    page=page,
                    limit=page_size,
                    total=total,
                    total_pages=total_pages
                ).dict(),
                summary={
                    "pendingRefunds": pending_refunds,
                    "approvedRefunds": approved_refunds,
                    "totalRefundAmount": total_refund_amount
                }
            ).dict(),
            message="获取退款申请列表成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refunds/{refund_id}/action", dependencies=[Depends(admin_route())])
async def process_refund_action(
    refund_id: str,
    action_request: RefundActionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """处理退款申请（管理员专用）"""
    try:
        refund = db.query(Refund).filter(Refund.refund_id == refund_id).first()
        if not refund:
            raise HTTPException(status_code=404, detail="退款申请不存在")
        
        # 验证操作类型
        valid_actions = ["approve", "reject", "complete"]
        if action_request.action not in valid_actions:
            raise HTTPException(status_code=400, detail="无效的操作类型")
        
        old_status = refund.status
        
        # 执行操作
        if action_request.action == "approve":
            refund.mark_as_approved(current_admin.id, action_request.adminNotes)
            
            # 更新订单状态为已退款
            order = db.query(Order).filter(Order.id == refund.order_id).first()
            if order:
                order.status = OrderStatus.REFUNDED.value
                
        elif action_request.action == "reject":
            refund.mark_as_rejected(current_admin.id, action_request.reason or action_request.adminNotes)
            
        elif action_request.action == "complete":
            if not action_request.externalRefundId:
                raise HTTPException(status_code=400, detail="完成退款需要提供外部退款ID")
            refund.mark_as_completed(action_request.externalRefundId)
        
        db.commit()
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="process_refund",
            target_type="refund",
            target_id=refund_id,
            details={
                "action": action_request.action,
                "oldStatus": old_status,
                "newStatus": refund.status,
                "reason": action_request.reason,
                "adminNotes": action_request.adminNotes,
                "externalRefundId": action_request.externalRefundId
            }
        )
        
        return SuccessResponse(
            data={
                "refundId": refund.refund_id,
                "action": action_request.action,
                "oldStatus": old_status,
                "newStatus": refund.status,
                "reason": action_request.reason,
                "adminNotes": action_request.adminNotes
            },
            message=f"退款申请已{action_request.action}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Dashboard Stats
@router.get("/dashboard/stats", dependencies=[Depends(admin_route())])
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取管理员仪表板统计数据"""
    try:
        # 用户统计
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        new_users_today = db.query(User).filter(
            User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # 会员统计
        membership_stats = {}
        for membership_type in MembershipType:
            count = db.query(User).filter(User.membership_type == membership_type).count()
            membership_stats[membership_type.value] = count
        
        # 积分统计
        total_credits = db.query(func.sum(User.credits)).scalar() or 0
        credit_transactions_today = db.query(CreditTransaction).filter(
            CreditTransaction.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        # 订单统计
        total_orders = db.query(Order).count()
        paid_orders = db.query(Order).filter(Order.status == OrderStatus.PAID.value).count()
        pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING.value).count()
        
        # 收入统计
        total_revenue = db.query(func.sum(Order.final_amount)).filter(
            Order.status == OrderStatus.PAID.value
        ).scalar() or 0
        
        revenue_today = db.query(func.sum(Order.final_amount)).filter(
            and_(
                Order.status == OrderStatus.PAID.value,
                Order.paid_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            )
        ).scalar() or 0
        
        # 退款统计
        pending_refunds = db.query(Refund).filter(Refund.status == "processing").count()
        total_refund_amount = db.query(func.sum(Refund.amount)).filter(
            Refund.status == "completed"
        ).scalar() or 0
        
        # 最近活动
        recent_orders = db.query(Order).join(User).order_by(desc(Order.created_at)).limit(5).all()
        recent_activity = []
        for order in recent_orders:
            recent_activity.append({
                "type": "order",
                "id": order.order_id,
                "user": order.user.email,
                "description": f"创建订单: {order.package_name}",
                "amount": order.final_amount / 100,  # 转换为元
                "status": order.status,
                "timestamp": order.created_at.isoformat()
            })
        
        recent_refunds = db.query(Refund).join(User).order_by(desc(Refund.created_at)).limit(3).all()
        for refund in recent_refunds:
            recent_activity.append({
                "type": "refund",
                "id": refund.refund_id,
                "user": refund.user.email,
                "description": f"申请退款: {refund.reason}",
                "amount": refund.amount / 100,  # 转换为元
                "status": refund.status,
                "timestamp": refund.created_at.isoformat()
            })
        
        # 按时间排序
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:8]  # 只取前8条
        
        # 记录审计日志
        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_dashboard",
            target_type="dashboard",
            target_id="stats",
            details={}
        )
        
        dashboard_stats = AdminDashboardStats(
            users={
                "total": total_users,
                "active": active_users,
                "admin": admin_users,
                "newToday": new_users_today,
                "membershipBreakdown": membership_stats
            },
            credits={
                "total": total_credits,
                "transactionsToday": credit_transactions_today
            },
            orders={
                "total": total_orders,
                "paid": paid_orders,
                "pending": pending_orders,
                "conversionRate": round(paid_orders / total_orders * 100, 2) if total_orders > 0 else 0
            },
            revenue={
                "total": total_revenue,
                "today": revenue_today,
                "averageOrderValue": round(total_revenue / paid_orders, 2) if paid_orders > 0 else 0
            },
            subscriptions={
                "pendingRefunds": pending_refunds,
                "totalRefundAmount": total_refund_amount
            },
            recentActivity=recent_activity
        )
        
        return SuccessResponse(
            data=dashboard_stats.dict(),
            message="获取仪表板统计成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/stats", dependencies=[Depends(admin_route())])
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db)
):
    """获取管理员仪表板统计数据"""
    try:
        # 用户统计
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        
        # 会员统计
        premium_users = db.query(User).filter(
            User.membership_type.in_([MembershipType.BASIC, MembershipType.PREMIUM, MembershipType.ENTERPRISE])
        ).count()
        
        # 积分统计
        from app.models.credit import CreditTransaction
        total_credits = db.query(User).with_entities(db.func.sum(User.credits)).scalar() or 0
        
        return SuccessResponse(
            data={
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "admin": admin_users,
                    "premium": premium_users
                },
                "credits": {
                    "total": total_credits
                }
            },
            message="获取仪表板统计成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
