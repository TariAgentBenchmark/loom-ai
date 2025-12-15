import uuid
import random
import string
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, condecimal
from datetime import datetime, timedelta
import re

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, MembershipType, UserStatus
from app.models.credit import CreditTransaction, CreditSource, TransactionType, CreditTransfer, CreditAlert
from app.models.payment import Order, Refund, OrderStatus, PackageType, PaymentMethod, Package
from app.models.task import Task
from app.models.agent import Agent, InvitationCode, AgentStatus, InvitationCodeStatus
from app.models.agent_commission import AgentCommission, AgentCommissionStatus
from app.api.dependencies import get_current_active_admin
from app.api.decorators import admin_required, admin_route
from app.schemas.common import SuccessResponse, PaginationMeta
from app.services.auth_service import AuthService
from app.services.api_limiter import api_limiter
from app.services.credit_math import to_decimal, to_float
from app.services.credit_service import CreditService
from app.services.membership_service import MembershipService

router = APIRouter()

CreditBalance = condecimal(max_digits=12, decimal_places=2, ge=0, le=1_000_000)
CreditDelta = condecimal(max_digits=12, decimal_places=2)


class AdminUserResponse(BaseModel):
    userId: str
    email: Optional[str]
    nickname: Optional[str]
    phone: Optional[str]
    agentId: Optional[int]
    agentName: Optional[str]
    invitationCode: Optional[str]
    credits: float
    membershipType: str
    status: str
    isAdmin: bool
    isTestUser: bool
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
    invitationCode: Optional[str] = Field(None, description="注册邀请码（可选）")
    isTestUser: bool = Field(False, description="是否为测试用户")


class AdminUserLookupItem(BaseModel):
    userId: str
    phone: Optional[str]
    email: Optional[str]
    nickname: Optional[str]


class AdminUserLookupResponse(BaseModel):
    users: List[AdminUserLookupItem]


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


class AdminUserTaskResponse(BaseModel):
    taskId: str
    type: str
    status: str
    creditsUsed: float
    createdAt: Optional[str]
    completedAt: Optional[str]
    originalFilename: Optional[str]
    resultFilename: Optional[str]


class AdminUserTaskListResponse(BaseModel):
    tasks: List[AdminUserTaskResponse]
    pagination: PaginationMeta
    pagination: PaginationMeta
    summary: Dict[str, Any]


class CreditAdjustmentRequest(BaseModel):
    amount: CreditDelta = Field(..., description="Amount to adjust (positive to add, negative to deduct)")
    reason: str = Field(..., description="Reason for adjustment")
    sendNotification: bool = Field(True, description="Send notification to user")


class AdminServicePriceResponse(BaseModel):
    serviceId: str
    serviceKey: str
    serviceName: str
    description: Optional[str]
    priceCredits: float
    active: bool
    createdAt: Optional[str]
    updatedAt: Optional[str]


class AdminServicePriceListResponse(BaseModel):
    services: List[AdminServicePriceResponse]


class AdminServicePriceUpdateRequest(BaseModel):
    priceCredits: condecimal(max_digits=12, decimal_places=2, ge=0)
    serviceName: Optional[str] = Field(None, max_length=100, description="Updated display name for the service")
    description: Optional[str] = Field(None, description="Service description")
    active: Optional[bool] = Field(None, description="Whether the service is active")


# Order Management Models
class AdminOrderResponse(BaseModel):
    orderId: str
    userId: str
    userEmail: Optional[str] = None
    userPhone: Optional[str] = None
    userNickname: Optional[str] = None
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


class ApiLimitMetric(BaseModel):
    api: str
    limit: int
    active: int
    available: int
    leasedTokens: int


class ApiLimitMetricsResponse(BaseModel):
    metrics: List[ApiLimitMetric]


class AdminAgentResponse(BaseModel):
    id: int
    name: str
    contact: Optional[str]
    notes: Optional[str]
    status: str
    level: int
    parentAgentId: Optional[int]
    ownerUserId: Optional[str]
    ownerUserPhone: Optional[str]
    createdAt: str
    updatedAt: Optional[str]
    invitationCode: Optional[str]
    invitationCount: int
    userCount: int


class AdminAgentListResponse(BaseModel):
    agents: List[AdminAgentResponse]


class AdminCreateAgentRequest(BaseModel):
    name: str = Field(..., max_length=100, description="代理商名称")
    userIdentifier: str = Field(..., description="绑定的已注册用户标识（userId/手机号/邮箱）")
    contact: Optional[str] = Field(None, max_length=100, description="联系人/联系方式")
    notes: Optional[str] = Field(None, max_length=500, description="备注")
    status: Optional[str] = Field(AgentStatus.ACTIVE.value, description="代理商状态")


class AdminDeleteAgentResponse(BaseModel):
    id: int
    name: str
    deleted: bool


class AdminSettleCommissionRequest(BaseModel):
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    orderIds: Optional[List[int]] = None
    note: Optional[str] = None


class AdminCommissionItem(BaseModel):
    orderId: str
    amount: int
    commission: int
    rate: float
    status: str
    paidAt: Optional[str]
    settledAt: Optional[str]
    settledBy: Optional[str]
    userId: Optional[str]
    userPhone: Optional[str]


class AdminCommissionListResponse(BaseModel):
    items: List[AdminCommissionItem]
    totalAmount: int
    totalCommission: int
    settledAmount: int
    unsettledAmount: int
    totalOrders: int


class AdminUpdateAgentRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    contact: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, description="代理商状态")


class AdminInvitationCodeResponse(BaseModel):
    id: int
    code: str
    agentId: int
    agentName: str
    status: str
    maxUses: Optional[int]
    usageCount: int
    remainingUses: Optional[int]
    expiresAt: Optional[str]
    description: Optional[str]
    createdAt: str


class AdminInvitationCodeListResponse(BaseModel):
    invitationCodes: List[AdminInvitationCodeResponse]


class AdminCreateInvitationCodeRequest(BaseModel):
    agentId: int = Field(..., description="所属代理商ID")
    description: Optional[str] = Field(None, max_length=255)
    maxUses: Optional[int] = Field(None, ge=0, description="最大使用次数，0或空为不限")
    expiresAt: Optional[str] = Field(None, description="过期时间，ISO8601")
    code: Optional[str] = Field(None, max_length=32, description="自定义邀请码，可留空自动生成")


class AdminUpdateInvitationCodeRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    maxUses: Optional[int] = Field(None, ge=0)
    expiresAt: Optional[str] = Field(None, description="过期时间，ISO8601，空字符串可清空")
    status: Optional[str] = Field(None, description="邀请码状态")


# Enhanced Dashboard Stats
class AdminDashboardStats(BaseModel):
    users: Dict[str, Any]
    credits: Dict[str, Any]
    orders: Dict[str, Any]
    revenue: Dict[str, Any]
    subscriptions: Dict[str, Any]
    recentActivity: List[Dict[str, Any]]


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if value == "":
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式无效，请使用 ISO8601 格式")


def _generate_invitation_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


def _compute_commission_cents(amount_cents: int) -> (int, float):
    """统一佣金计算：<= 30000 抽20%，超过部分抽25%"""
    amt = Decimal(amount_cents or 0)
    if amt <= 0:
        return 0, 0.0
    threshold_cents = Decimal("30000") * 100
    lower = min(amt, threshold_cents)
    higher = max(amt - threshold_cents, 0)
    commission = lower * Decimal("0.20") + higher * Decimal("0.25")
    commission = commission.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    eff_rate = float((commission / amt).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    return int(commission), eff_rate


def _compute_commission_running_total(order_rows: List[tuple]) -> Dict[int, Dict[str, float]]:
    """
    按代理累计充值计算佣金：前 30000 元按 20%，超过部分按 25%。
    返回 {order_id: {"commission": int, "rate": float}}，顺序根据支付时间。
    """
    threshold_cents = Decimal("30000") * 100
    cumulative = Decimal("0")
    result: Dict[int, Dict[str, float]] = {}

    def _order_key(order: Order):
        # 以 paid_at 优先，其次 created_at 兜底
        return order.paid_at or order.created_at or datetime.utcnow()

    for order, _user in sorted(order_rows, key=lambda row: _order_key(row[0])):
        amount = Decimal(order.final_amount or 0)
        if amount <= 0:
            result[order.id] = {"commission": 0, "rate": 0.0}
            continue

        remaining_lower = max(threshold_cents - cumulative, Decimal("0"))
        lower_part = min(amount, remaining_lower)
        higher_part = max(amount - remaining_lower, Decimal("0"))
        commission = lower_part * Decimal("0.20") + higher_part * Decimal("0.25")
        commission = commission.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        eff_rate = float((commission / amount).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))

        result[order.id] = {"commission": int(commission), "rate": eff_rate}
        cumulative += amount

    return result


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
            agent_name = user.agent.name if user.agent else None
            invitation_code_value = user.invitation_code.code if user.invitation_code else None
            user_list.append(AdminUserResponse(
                userId=user.user_id,
                email=user.email,
                nickname=user.nickname,
                phone=user.phone,
                agentId=user.agent_id,
                agentName=agent_name,
                invitationCode=invitation_code_value,
                credits=to_float(user.credits),
                membershipType=user.membership_type.value,
                status=user.status.value,
                isAdmin=user.is_admin,
                isTestUser=bool(getattr(user, "is_test_user", False)),
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


@router.get("/users/search", dependencies=[Depends(admin_route())])
async def search_users(
    q: str = Query(..., min_length=1, description="用户ID/手机号/邮箱搜索关键字"),
    limit: int = Query(10, ge=1, le=50, description="返回条数上限"),
    db: Session = Depends(get_db),
):
    """模糊搜索用户以供选择"""
    try:
        keyword = q.strip()
        digits_only = re.sub(r"\D", "", keyword)
        query = (
            db.query(User)
            .filter(
                or_(
                    User.user_id.ilike(f"%{keyword}%"),
                    User.phone.ilike(f"%{keyword}%"),
                    User.email.ilike(f"%{keyword}%"),
                    *( [User.phone == digits_only] if digits_only else [] ),
                )
            )
            .order_by(desc(User.created_at))
            .limit(limit)
        )
        users = query.all()

        return SuccessResponse(
            data=AdminUserLookupResponse(
                users=[
                    AdminUserLookupItem(
                        userId=user.user_id,
                        phone=user.phone,
                        email=user.email,
                        nickname=user.nickname,
                    )
                    for user in users
                ]
            ).dict(),
            message="用户搜索成功",
        )
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
        
        agent_name = user.agent.name if user.agent else None
        invitation_code_value = user.invitation_code.code if user.invitation_code else None

        user_detail = AdminUserResponse(
            userId=user.user_id,
            email=user.email,
            nickname=user.nickname,
            phone=user.phone,
            agentId=user.agent_id,
            agentName=agent_name,
            invitationCode=invitation_code_value,
            credits=to_float(user.credits),
            membershipType=user.membership_type.value,
            status=user.status.value,
            isAdmin=user.is_admin,
            isTestUser=bool(getattr(user, "is_test_user", False)),
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


@router.get("/users/{user_id}/tasks", dependencies=[Depends(admin_route())])
async def get_user_tasks(
    user_id: str,
    type: Optional[str] = Query(None, description="任务类型"),
    status: Optional[str] = Query(None, description="任务状态"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取指定用户的任务历史（管理员专用）"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        query = db.query(Task).filter(Task.user_id == user.id)
        if type:
            query = query.filter(Task.type == type)
        if status:
            query = query.filter(Task.status == status)

        total = query.count()
        tasks = (
            query.order_by(desc(Task.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return SuccessResponse(
            data=AdminUserTaskListResponse(
                tasks=[
                    AdminUserTaskResponse(
                        taskId=task.task_id,
                        type=task.type,
                        status=task.status,
                        creditsUsed=to_float(task.credits_used),
                        createdAt=task.created_at.isoformat() if task.created_at else None,
                        completedAt=task.completed_at.isoformat() if task.completed_at else None,
                        originalFilename=task.original_filename,
                        resultFilename=task.result_filename,
                    )
                    for task in tasks
                ],
                pagination=PaginationMeta(
                    page=page,
                    limit=limit,
                    total=total,
                    total_pages=(total + limit - 1) // limit,
                ),
            ).dict(),
            message="获取用户任务历史成功",
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

        agent_id = None
        invitation_code_id = None
        if user_data.invitationCode:
            code_value = user_data.invitationCode.strip().upper()
            code_record = (
                db.query(InvitationCode)
                .filter(InvitationCode.code == code_value, InvitationCode.is_deleted.is_(False))
                .first()
            )
            if not code_record:
                raise HTTPException(status_code=400, detail="邀请码无效")
            if code_record.status != InvitationCodeStatus.ACTIVE:
                raise HTTPException(status_code=400, detail="邀请码已被停用")
            if code_record.expires_at and code_record.expires_at <= datetime.utcnow():
                raise HTTPException(status_code=400, detail="邀请码已过期")
            if code_record.max_uses not in (None, 0) and (code_record.usage_count or 0) >= code_record.max_uses:
                raise HTTPException(status_code=400, detail="邀请码已达使用上限")

            agent = (
                db.query(Agent)
                .filter(Agent.id == code_record.agent_id, Agent.is_deleted.is_(False))
                .first()
            )
            if not agent or agent.status != AgentStatus.ACTIVE:
                raise HTTPException(status_code=400, detail="所属代理商不可用")

            agent_id = agent.id
            invitation_code_id = code_record.id

        user = User(
            user_id=f"user_{uuid.uuid4().hex[:12]}",
            phone=user_data.phone,
            email=user_data.email,
            nickname=user_data.nickname or user_data.phone,
            hashed_password=auth_service.get_password_hash(user_data.password),
            credits=to_decimal(user_data.initialCredits),
            membership_type=MembershipType.FREE,
            status=UserStatus.ACTIVE,
            is_admin=user_data.isAdmin,
            is_test_user=user_data.isTestUser,
            agent_id=agent_id,
            invitation_code_id=invitation_code_id,
        )

        db.add(user)
        if invitation_code_id:
            code_record.usage_count = (code_record.usage_count or 0) + 1
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
                phone=user.phone,
                agentId=user.agent_id,
                agentName=None,
                invitationCode=None,
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
    except IntegrityError as ie:
        db.rollback()
        msg = str(ie.orig).lower()
        if "agents_name_key" in msg or "unique constraint" in msg:
            raise HTTPException(status_code=400, detail="代理商名称已存在")
        raise HTTPException(status_code=400, detail="创建代理商失败，数据唯一性冲突")
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


# Service Pricing Management
@router.get("/service-prices", dependencies=[Depends(admin_route())])
async def get_service_prices_admin(
    include_inactive: bool = Query(True, description="Whether to include inactive services"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取所有功能的积分价格（管理员专用）"""
    try:
        membership_service = MembershipService()
        services = await membership_service.get_service_prices(
            db=db,
            include_inactive=include_inactive
        )

        service_items = [
            AdminServicePriceResponse(
                serviceId=item["service_id"],
                serviceKey=item["service_key"],
                serviceName=item["service_name"],
                description=item.get("description"),
                priceCredits=item["price_credits"],
                active=item["active"],
                createdAt=item.get("created_at"),
                updatedAt=item.get("updated_at")
            )
            for item in services
        ]

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="view_service_prices",
            target_type="service_price",
            target_id="list",
            details={
                "include_inactive": include_inactive,
                "total": len(service_items)
            }
        )

        return SuccessResponse(
            data=AdminServicePriceListResponse(services=service_items).dict(),
            message="获取服务价格列表成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/service-prices/{service_key}", dependencies=[Depends(admin_route())])
async def update_service_price_admin(
    service_key: str,
    update_request: AdminServicePriceUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """更新指定功能的积分价格（管理员专用）"""
    try:
        membership_service = MembershipService()

        update_result = await membership_service.update_service_price(
            db=db,
            service_key=service_key,
            price_credits=update_request.priceCredits,
            service_name=update_request.serviceName,
            description=update_request.description,
            active=update_request.active
        )

        service_data_raw = update_result["service"]
        service_data = AdminServicePriceResponse(
            serviceId=service_data_raw["service_id"],
            serviceKey=service_data_raw["service_key"],
            serviceName=service_data_raw["service_name"],
            description=service_data_raw.get("description"),
            priceCredits=service_data_raw["price_credits"],
            active=service_data_raw["active"],
            createdAt=service_data_raw.get("created_at"),
            updatedAt=service_data_raw.get("updated_at")
        )

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="update_service_price",
            target_type="service_price",
            target_id=service_key,
            details={
                "changes": update_result.get("changes", {}),
                "priceCredits": to_float(update_request.priceCredits),
                "serviceName": update_request.serviceName,
                "active": update_request.active
            }
        )

        return SuccessResponse(
            data={
                "service": service_data.dict(),
                "changes": update_result.get("changes", {}),
                "updated": update_result.get("updated", False)
            },
            message="服务价格更新成功"
        )

    except ValueError:
        raise HTTPException(status_code=404, detail="服务不存在")
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

        # 补齐缺失的积分交易记录（早期订单可能未写入流水）
        paid_orders = (
            db.query(Order)
            .filter(
                Order.user_id == user.id,
                Order.status == OrderStatus.PAID.value,
                Order.credits_amount.isnot(None),
                Order.credits_amount > 0,
            )
            .all()
        )
        if paid_orders:
            existing_order_txns = {
                oid
                for (oid,) in db.query(CreditTransaction.related_order_id)
                .filter(
                    CreditTransaction.user_id == user.id,
                    CreditTransaction.related_order_id.isnot(None),
                )
                .all()
                if oid
            }
            credit_service = CreditService()
            for order in paid_orders:
                if order.order_id in existing_order_txns:
                    continue
                await credit_service.record_transaction(
                    db=db,
                    user_id=user.id,
                    amount=order.credits_amount,
                    source=CreditSource.PURCHASE.value,
                    description=f"购买 {order.package_name or order.package_id or '套餐'} (补记)",
                    related_order_id=order.order_id,
                )
        
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
                userEmail=order.user.email or None,
                userPhone=order.user.phone or None,
                userNickname=order.user.nickname or None,
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
            userEmail=order.user.email or None,
            userPhone=order.user.phone or None,
            userNickname=order.user.nickname or None,
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

            # 如果是积分套餐或之前遗留的未标记套餐，但携带积分数量，则加积分
            if order.credits_amount and order.credits_amount > 0:
                user = db.query(User).filter(User.id == order.user_id).first()
                if user:
                    # 补充订单的套餐类型标记，方便后续统计
                    if not order.package_type:
                        order.package_type = PackageType.CREDITS.value
                    from app.services.credit_service import CreditService
                    credit_service = CreditService()
                    await credit_service.add_credits_from_purchase(
                        db=db,
                        user_id=user.id,
                        amount=order.credits_amount,
                        order_id=order.order_id,
                        package_name=order.package_name
                    )

            # 会员套餐处理
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


@router.get("/agents", dependencies=[Depends(admin_route())])
async def list_agents(
    status: Optional[str] = Query(None, description="Filter by agent status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """代理商列表"""
    try:
        query = db.query(Agent).filter(Agent.is_deleted.is_(False))
        if status:
            try:
                status_enum = AgentStatus(status)
                query = query.filter(Agent.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的代理商状态")

        agents = query.order_by(desc(Agent.created_at)).all()

        owner_ids = [agent.owner_user_id for agent in agents if agent.owner_user_id]
        owner_map = {
            user.id: user
            for user in db.query(User.id, User.user_id, User.phone)
            .filter(User.id.in_(owner_ids))
            .all()
        } if owner_ids else {}

        invitation_counts = {
            agent_id: count
            for agent_id, count in db.query(
                InvitationCode.agent_id, func.count(InvitationCode.id)
            )
            .filter(InvitationCode.is_deleted.is_(False))
            .group_by(InvitationCode.agent_id)
            .all()
        }
        user_counts = {
            agent_id: count
            for agent_id, count in db.query(User.agent_id, func.count(User.id))
            .filter(User.agent_id.isnot(None))
            .group_by(User.agent_id)
            .all()
        }

        response_items = [
            AdminAgentResponse(
                id=agent.id,
                name=agent.name,
                contact=agent.contact,
                notes=agent.notes,
                status=agent.status.value if agent.status else AgentStatus.ACTIVE.value,
                level=agent.level or 1,
                parentAgentId=agent.parent_agent_id,
                ownerUserId=owner_map.get(agent.owner_user_id).user_id if agent.owner_user_id and agent.owner_user_id in owner_map else None,
                ownerUserPhone=owner_map.get(agent.owner_user_id).phone if agent.owner_user_id and agent.owner_user_id in owner_map else None,
                createdAt=agent.created_at.isoformat() if agent.created_at else "",
                updatedAt=agent.updated_at.isoformat() if agent.updated_at else None,
                invitationCode=(
                    agent.invitation_codes[0].code if agent.invitation_codes else None
                ),
                invitationCount=invitation_counts.get(agent.id, 0),
                userCount=user_counts.get(agent.id, 0),
            )
            for agent in agents
        ]

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="list_agents",
            target_type="agent",
            target_id="list",
            details={"status": status},
        )

        return SuccessResponse(
            data=AdminAgentListResponse(agents=response_items).dict(),
            message="获取代理商列表成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents", dependencies=[Depends(admin_route())])
async def create_agent(
    payload: AdminCreateAgentRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """创建代理商"""
    try:
        existing = (
            db.query(Agent)
            .filter(Agent.name == payload.name, Agent.is_deleted.is_(False))
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="代理商名称已存在")

        owner_user = (
            db.query(User)
            .filter(
                or_(
                    User.user_id == payload.userIdentifier,
                    User.phone == payload.userIdentifier,
                    User.email == payload.userIdentifier,
                )
            )
            .first()
        )
        if not owner_user:
            raise HTTPException(status_code=404, detail="绑定用户不存在")

        owned_agent = (
            db.query(Agent)
            .filter(Agent.owner_user_id == owner_user.id, Agent.is_deleted.is_(False))
            .first()
        )
        if owned_agent:
            raise HTTPException(status_code=400, detail="该用户已绑定其他代理商")

        status_value = AgentStatus(payload.status) if payload.status else AgentStatus.ACTIVE

        agent = Agent(
            name=payload.name,
            owner_user_id=owner_user.id,
            contact=payload.contact,
            notes=payload.notes,
            status=status_value,
        )
        db.add(agent)
        db.flush()

        code = _generate_invitation_code()
        invite = InvitationCode(
            code=code,
            agent_id=agent.id,
            status=InvitationCodeStatus.ACTIVE,
        )
        db.add(invite)

        db.commit()
        db.refresh(agent)
        db.refresh(invite)

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="create_agent",
            target_type="agent",
            target_id=str(agent.id),
            details={
                "name": agent.name,
                "status": agent.status.value,
                "ownerUserId": owner_user.user_id,
            },
        )

        return SuccessResponse(
            data=AdminAgentResponse(
                id=agent.id,
                name=agent.name,
                contact=agent.contact,
                notes=agent.notes,
                status=agent.status.value,
                level=agent.level or 1,
                parentAgentId=agent.parent_agent_id,
                ownerUserId=owner_user.user_id,
                ownerUserPhone=owner_user.phone,
                createdAt=agent.created_at.isoformat() if agent.created_at else "",
                updatedAt=agent.updated_at.isoformat() if agent.updated_at else None,
                invitationCode=invite.code,
                invitationCount=0,
                userCount=0,
            ).dict(),
            message="代理商创建成功",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_id}", dependencies=[Depends(admin_route())])
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """删除代理商（仅限停用状态）"""
    try:
        agent = (
            db.query(Agent)
            .filter(Agent.id == agent_id, Agent.is_deleted.is_(False))
            .first()
        )
        if not agent:
            raise HTTPException(status_code=404, detail="代理商不存在")
        if agent.status != AgentStatus.DISABLED:
            raise HTTPException(status_code=400, detail="请先停用代理商后再删除")

        agent.is_deleted = True
        # 同时停用邀请码
        for code in agent.invitation_codes:
            code.is_deleted = True
            code.status = InvitationCodeStatus.DISABLED

        db.commit()

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="delete_agent",
            target_type="agent",
            target_id=str(agent.id),
            details={"name": agent.name},
        )

        return SuccessResponse(
            data=AdminDeleteAgentResponse(id=agent.id, name=agent.name, deleted=True).dict(),
            message="代理商已删除",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/commissions/settle", dependencies=[Depends(admin_route())])
async def settle_agent_commissions(
    agent_id: int,
    payload: AdminSettleCommissionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """管理员手动结算代理商佣金"""
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id, Agent.is_deleted.is_(False))
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="代理商不存在")

    start_dt = datetime.fromisoformat(payload.startDate) if payload.startDate else None
    end_dt = datetime.fromisoformat(payload.endDate) if payload.endDate else None

    # 找到已付款订单
    order_query = (
        db.query(Order, User)
        .join(User, User.id == Order.user_id)
        .filter(
            User.agent_id == agent.id,
            Order.status == OrderStatus.PAID.value,
        )
    )
    if start_dt:
        order_query = order_query.filter(Order.paid_at >= start_dt)
    if end_dt:
        order_query = order_query.filter(Order.paid_at <= end_dt)
    if payload.orderIds:
        order_query = order_query.filter(Order.id.in_(payload.orderIds))

    rows = order_query.all()

    if not rows:
        return SuccessResponse(data={"settled": 0, "totalOrders": 0}, message="无可结算订单")

    commission_map = _compute_commission_running_total(rows)

    # 已结算的订单
    existing_map = {
        c.order_id: c for c in db.query(AgentCommission).filter(
            AgentCommission.order_id.in_([r[0].id for r in rows]),
            AgentCommission.status == AgentCommissionStatus.SETTLED,
        )
    }

    settled_amount = 0
    settled_count = 0
    for order, _user in rows:
        if order.id in existing_map:
            continue
        computed = commission_map.get(order.id, {"commission": 0, "rate": 0.0})
        commission = computed.get("commission", 0)
        rate = computed.get("rate", 0.0)
        record = AgentCommission(
            agent_id=agent.id,
            order_id=order.id,
            amount=commission,
            rate=rate,
            status=AgentCommissionStatus.SETTLED,
            paid_at=order.paid_at,
            settled_at=datetime.utcnow(),
            settled_by=current_admin.id,
            notes=payload.note,
        )
        db.add(record)
        settled_amount += commission
        settled_count += 1

    db.commit()

    await log_admin_action(
        db=db,
        admin=current_admin,
        action="settle_agent_commission",
        target_type="agent",
        target_id=str(agent.id),
        details={"orders": settled_count, "amount": settled_amount},
    )

    return SuccessResponse(
        data={
            "settledOrders": settled_count,
            "settledAmount": settled_amount,
        },
        message="佣金结算完成",
    )


@router.get("/agents/{agent_id}/commissions", dependencies=[Depends(admin_route())])
async def get_agent_commissions(
    agent_id: int,
    startDate: Optional[str] = Query(None, description="开始日期，ISO8601"),
    endDate: Optional[str] = Query(None, description="结束日期，ISO8601"),
    status: Optional[str] = Query(None, description="过滤状态：settled/unsettled"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """管理员查看代理商佣金流水（含结算状态）"""
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id, Agent.is_deleted.is_(False))
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="代理商不存在")

    start_dt = _parse_iso_datetime(startDate)
    end_dt = _parse_iso_datetime(endDate)

    order_query = (
        db.query(Order, User)
        .join(User, User.id == Order.user_id)
        .filter(
            User.agent_id == agent.id,
            Order.status == OrderStatus.PAID.value,
        )
    )
    if start_dt:
        order_query = order_query.filter(Order.paid_at >= start_dt)
    if end_dt:
        order_query = order_query.filter(Order.paid_at <= end_dt)

    order_rows = order_query.order_by(desc(Order.paid_at)).all()
    if not order_rows:
        return SuccessResponse(
            data=AdminCommissionListResponse(
                items=[],
                totalAmount=0,
                totalCommission=0,
                settledAmount=0,
                unsettledAmount=0,
                totalOrders=0,
            ).dict(),
            message="暂无佣金流水",
        )

    order_ids = [o.id for o, _u in order_rows]
    commission_query = db.query(AgentCommission).filter(
        AgentCommission.agent_id == agent.id,
        AgentCommission.order_id.in_(order_ids),
    )
    if status in {AgentCommissionStatus.SETTLED, AgentCommissionStatus.UNSETTLED}:
        commission_query = commission_query.filter(AgentCommission.status == status)
    commission_map = {c.order_id: c for c in commission_query.all()}

    items: List[AdminCommissionItem] = []
    total_amount = 0
    total_commission = 0
    settled_amount = 0

    computed_map = _compute_commission_running_total(order_rows)

    for order, user in order_rows:
        record = commission_map.get(order.id)
        amount = order.final_amount or 0

        computed = computed_map.get(order.id, {"commission": 0, "rate": 0.0})
        commission_amt = int(computed["commission"])
        rate = float(computed["rate"])
        current_status = AgentCommissionStatus.UNSETTLED
        settled_at = None
        settled_by = None

        if record:
            current_status = record.status
            settled_at = record.settled_at.isoformat() if record.settled_at else None
            if record.settled_by:
                admin_user = db.query(User).filter(User.id == record.settled_by).first()
                settled_by = admin_user.user_id if admin_user else None
            if record.amount is not None:
                commission_amt = int(record.amount)

        # 如果传入状态过滤，且当前状态不匹配则跳过
        if status and current_status != status:
            continue

        total_amount += amount
        total_commission += commission_amt
        if current_status == AgentCommissionStatus.SETTLED:
            settled_amount += commission_amt

        items.append(
            AdminCommissionItem(
                orderId=order.order_id,
                amount=amount,
                commission=commission_amt,
                rate=rate,
                status=current_status,
                paidAt=order.paid_at.isoformat() if order.paid_at else None,
                settledAt=settled_at,
                settledBy=settled_by,
                userId=user.user_id,
                userPhone=user.phone,
            )
        )

    unsettled_amount = max(total_commission - settled_amount, 0)

    await log_admin_action(
        db=db,
        admin=current_admin,
        action="view_agent_commissions",
        target_type="agent",
        target_id=str(agent.id),
        details={
            "orders": len(items),
            "totalAmount": total_amount,
            "totalCommission": total_commission,
            "statusFilter": status,
        },
    )

    return SuccessResponse(
        data=AdminCommissionListResponse(
            items=items,
            totalAmount=total_amount,
            totalCommission=total_commission,
            settledAmount=settled_amount,
            unsettledAmount=unsettled_amount,
            totalOrders=len(items),
        ).dict(),
        message="获取佣金流水成功",
    )


@router.post("/agents/{agent_id}/commissions/{order_id}/settle", dependencies=[Depends(admin_route())])
async def settle_single_commission(
    agent_id: int,
    order_id: str,
    payload: AdminSettleCommissionRequest = Body(default_factory=AdminSettleCommissionRequest),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """管理员手动结算单笔订单佣金"""
    agent = (
        db.query(Agent)
        .filter(Agent.id == agent_id, Agent.is_deleted.is_(False))
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="代理商不存在")

    order_rows = (
        db.query(Order, User)
        .join(User, User.id == Order.user_id)
        .filter(
            User.agent_id == agent.id,
            Order.status == OrderStatus.PAID.value,
        )
        .all()
    )
    if not order_rows:
        raise HTTPException(status_code=404, detail="订单不存在或未归属该代理")

    commission_map = _compute_commission_running_total(order_rows)
    order = (
        db.query(Order)
        .filter(Order.order_id == order_id, Order.status == OrderStatus.PAID.value)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在或未归属该代理")

    computed = commission_map.get(order.id, {"commission": 0, "rate": 0.0})
    commission = computed.get("commission", 0)
    rate = computed.get("rate", 0.0)

    record = (
        db.query(AgentCommission)
        .filter(AgentCommission.agent_id == agent.id, AgentCommission.order_id == order.id)
        .first()
    )
    now = datetime.utcnow()
    if record:
        record.amount = commission
        record.rate = rate
        record.status = AgentCommissionStatus.SETTLED
        record.paid_at = order.paid_at
        record.settled_at = now
        record.settled_by = current_admin.id
        record.notes = payload.note
    else:
        record = AgentCommission(
            agent_id=agent.id,
            order_id=order.id,
            amount=commission,
            rate=rate,
            status=AgentCommissionStatus.SETTLED,
            paid_at=order.paid_at,
            settled_at=now,
            settled_by=current_admin.id,
            notes=payload.note,
        )
        db.add(record)

    db.commit()

    await log_admin_action(
        db=db,
        admin=current_admin,
        action="settle_agent_commission_single",
        target_type="agent",
        target_id=str(agent.id),
        details={"orderId": order_id, "amount": commission},
    )

    return SuccessResponse(
        data={
            "orderId": order.order_id,
            "commission": commission,
            "settled": True,
        },
        message="单笔佣金结算完成",
    )


@router.put("/agents/{agent_id}", dependencies=[Depends(admin_route())])
async def update_agent(
    agent_id: int,
    payload: AdminUpdateAgentRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """更新代理商信息"""
    try:
        agent = (
            db.query(Agent)
            .filter(Agent.id == agent_id, Agent.is_deleted.is_(False))
            .first()
        )
        if not agent:
            raise HTTPException(status_code=404, detail="代理商不存在")

        if payload.name and payload.name != agent.name:
            duplicate = (
                db.query(Agent)
                .filter(Agent.name == payload.name, Agent.id != agent_id, Agent.is_deleted.is_(False))
                .first()
            )
            if duplicate:
                raise HTTPException(status_code=400, detail="代理商名称已存在")
            agent.name = payload.name

        if payload.contact is not None:
            agent.contact = payload.contact
        if payload.notes is not None:
            agent.notes = payload.notes
        if payload.status:
            try:
                agent.status = AgentStatus(payload.status)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的代理商状态")

        db.commit()
        db.refresh(agent)

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="update_agent",
            target_type="agent",
            target_id=str(agent.id),
            details=payload.dict(),
        )

        return SuccessResponse(
            data=AdminAgentResponse(
                id=agent.id,
                name=agent.name,
                contact=agent.contact,
                notes=agent.notes,
                status=agent.status.value if agent.status else AgentStatus.ACTIVE.value,
                level=agent.level or 1,
                parentAgentId=agent.parent_agent_id,
                ownerUserId=agent.owner_user.user_id if agent.owner_user else None,
                ownerUserPhone=agent.owner_user.phone if agent.owner_user else None,
                createdAt=agent.created_at.isoformat() if agent.created_at else "",
                updatedAt=agent.updated_at.isoformat() if agent.updated_at else None,
                invitationCode=(
                    agent.invitation_codes[0].code if agent.invitation_codes else None
                ),
                invitationCount=(
                    db.query(InvitationCode)
                    .filter(InvitationCode.agent_id == agent.id, InvitationCode.is_deleted.is_(False))
                    .count()
                ),
                userCount=db.query(User).filter(User.agent_id == agent.id).count(),
            ).dict(),
            message="代理商更新成功",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/users", dependencies=[Depends(admin_route())])
async def list_agent_users(
    agent_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """查看代理商旗下用户"""
    try:
        agent = (
            db.query(Agent)
            .filter(Agent.id == agent_id, Agent.is_deleted.is_(False))
            .first()
        )
        if not agent:
            raise HTTPException(status_code=404, detail="代理商不存在")

        users = (
            db.query(User)
            .filter(User.agent_id == agent_id)
            .order_by(desc(User.created_at))
            .all()
        )

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="list_agent_users",
            target_type="agent",
            target_id=str(agent_id),
            details={"userCount": len(users)},
        )

        return SuccessResponse(
            data={
                "agent": {
                    "id": agent.id,
                    "name": agent.name,
                    "status": agent.status.value if agent.status else AgentStatus.ACTIVE.value,
                },
                "users": [
                    {
                        "userId": user.user_id,
                        "email": user.email,
                        "phone": user.phone,
                        "nickname": user.nickname,
                        "createdAt": user.created_at.isoformat() if user.created_at else "",
                    }
                    for user in users
                ],
            },
            message="获取代理商用户成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invitation-codes", dependencies=[Depends(admin_route())])
async def list_invitation_codes(
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    code_search: Optional[str] = Query(None, description="模糊搜索邀请码"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """邀请码列表"""
    try:
        query = (
            db.query(InvitationCode)
            .filter(InvitationCode.is_deleted.is_(False))
            .order_by(desc(InvitationCode.created_at))
        )
        if agent_id:
            query = query.filter(InvitationCode.agent_id == agent_id)
        if status:
            try:
                status_enum = InvitationCodeStatus(status)
                query = query.filter(InvitationCode.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的邀请码状态")
        if code_search:
            query = query.filter(InvitationCode.code.ilike(f"%{code_search}%"))

        codes = query.all()
        agent_map = {
            agent.id: agent.name
            for agent in db.query(Agent.id, Agent.name)
            .filter(Agent.is_deleted.is_(False))
            .all()
        }

        response_items = []
        for code in codes:
            remaining = None
            if code.max_uses not in (None, 0):
                remaining = max((code.max_uses or 0) - (code.usage_count or 0), 0)

            response_items.append(
                AdminInvitationCodeResponse(
                    id=code.id,
                    code=code.code,
                    agentId=code.agent_id,
                    agentName=agent_map.get(code.agent_id, ""),
                    status=code.status.value if code.status else InvitationCodeStatus.ACTIVE.value,
                    maxUses=code.max_uses,
                    usageCount=code.usage_count or 0,
                    remainingUses=remaining,
                    expiresAt=code.expires_at.isoformat() if code.expires_at else None,
                    description=code.description,
                    createdAt=code.created_at.isoformat() if code.created_at else "",
                )
            )

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="list_invitation_codes",
            target_type="invitation_code",
            target_id="list",
            details={"agent_id": agent_id, "status": status},
        )

        return SuccessResponse(
            data=AdminInvitationCodeListResponse(invitationCodes=response_items).dict(),
            message="获取邀请码列表成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invitation-codes", dependencies=[Depends(admin_route())])
async def create_invitation_code(
    payload: AdminCreateInvitationCodeRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """创建邀请码"""
    try:
        agent = (
            db.query(Agent)
            .filter(Agent.id == payload.agentId, Agent.is_deleted.is_(False))
            .first()
        )
        if not agent:
            raise HTTPException(status_code=404, detail="代理商不存在")

        new_code = (payload.code or _generate_invitation_code()).upper()
        exists = db.query(InvitationCode).filter(InvitationCode.code == new_code).first()
        if exists:
            raise HTTPException(status_code=400, detail="邀请码已存在，请换一个")

        expires_at = _parse_iso_datetime(payload.expiresAt)

        invitation = InvitationCode(
            code=new_code,
            agent_id=payload.agentId,
            description=payload.description,
            max_uses=payload.maxUses,
            expires_at=expires_at,
            status=InvitationCodeStatus.ACTIVE,
        )
        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="create_invitation_code",
            target_type="invitation_code",
            target_id=str(invitation.id),
            details={
                "agentId": payload.agentId,
                "code": new_code,
                "maxUses": payload.maxUses,
                "expiresAt": payload.expiresAt,
            },
        )

        return SuccessResponse(
            data=AdminInvitationCodeResponse(
                id=invitation.id,
                code=invitation.code,
                agentId=invitation.agent_id,
                agentName=agent.name,
                status=invitation.status.value,
                maxUses=invitation.max_uses,
                usageCount=invitation.usage_count or 0,
                remainingUses=(
                    None
                    if invitation.max_uses in (None, 0)
                    else max((invitation.max_uses or 0) - (invitation.usage_count or 0), 0)
                ),
                expiresAt=invitation.expires_at.isoformat() if invitation.expires_at else None,
                description=invitation.description,
                createdAt=invitation.created_at.isoformat() if invitation.created_at else "",
            ).dict(),
            message="邀请码创建成功",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/invitation-codes/{code_id}", dependencies=[Depends(admin_route())])
async def update_invitation_code(
    code_id: int,
    payload: AdminUpdateInvitationCodeRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin),
):
    """更新邀请码状态或限制"""
    try:
        invitation = (
            db.query(InvitationCode)
            .filter(InvitationCode.id == code_id, InvitationCode.is_deleted.is_(False))
            .first()
        )
        if not invitation:
            raise HTTPException(status_code=404, detail="邀请码不存在")

        if payload.description is not None:
            invitation.description = payload.description
        if payload.maxUses is not None:
            invitation.max_uses = payload.maxUses
        if payload.expiresAt is not None:
            invitation.expires_at = _parse_iso_datetime(payload.expiresAt)
        if payload.status:
            try:
                invitation.status = InvitationCodeStatus(payload.status)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的邀请码状态")

        db.commit()
        db.refresh(invitation)

        agent = db.query(Agent).filter(Agent.id == invitation.agent_id).first()

        await log_admin_action(
            db=db,
            admin=current_admin,
            action="update_invitation_code",
            target_type="invitation_code",
            target_id=str(code_id),
            details=payload.dict(),
        )

        remaining = None
        if invitation.max_uses not in (None, 0):
            remaining = max((invitation.max_uses or 0) - (invitation.usage_count or 0), 0)

        return SuccessResponse(
            data=AdminInvitationCodeResponse(
                id=invitation.id,
                code=invitation.code,
                agentId=invitation.agent_id,
                agentName=agent.name if agent else "",
                status=invitation.status.value if invitation.status else InvitationCodeStatus.ACTIVE.value,
                maxUses=invitation.max_uses,
                usageCount=invitation.usage_count or 0,
                remainingUses=remaining,
                expiresAt=invitation.expires_at.isoformat() if invitation.expires_at else None,
                description=invitation.description,
                createdAt=invitation.created_at.isoformat() if invitation.created_at else "",
            ).dict(),
            message="邀请码更新成功",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Enhanced Dashboard Stats
@router.get("/dashboard/stats", dependencies=[Depends(admin_route())])
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """获取管理员仪表板统计数据"""
    try:
        non_admin_filter = User.is_admin.is_(False)
        
        # 用户统计
        total_users = db.query(User).filter(non_admin_filter).count()
        active_users = db.query(User).filter(User.status == UserStatus.ACTIVE, non_admin_filter).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        new_users_today = db.query(User).filter(
            User.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            non_admin_filter
        ).count()
        
        # 会员统计
        membership_stats = {}
        for membership_type in MembershipType:
            count = db.query(User).filter(
                User.membership_type == membership_type,
                non_admin_filter
            ).count()
            membership_stats[membership_type.value] = count
        
        # 积分统计
        total_credits = db.query(func.sum(User.credits)).filter(non_admin_filter).scalar() or 0
        credit_transactions_today = db.query(CreditTransaction).join(
            User, CreditTransaction.user_id == User.id
        ).filter(
            CreditTransaction.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            non_admin_filter
        ).count()
        
        # 订单统计
        base_order_query = db.query(Order).join(User).filter(non_admin_filter)
        total_orders = base_order_query.count()
        paid_orders = base_order_query.filter(Order.status == OrderStatus.PAID.value).count()
        pending_orders = base_order_query.filter(Order.status == OrderStatus.PENDING.value).count()
        
        # 收入统计
        total_revenue = db.query(func.sum(Order.final_amount)).join(User).filter(
            Order.status == OrderStatus.PAID.value,
            non_admin_filter
        ).scalar() or 0
        
        revenue_today = db.query(func.sum(Order.final_amount)).join(User).filter(
            and_(
                Order.status == OrderStatus.PAID.value,
                Order.paid_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ),
            non_admin_filter
        ).scalar() or 0
        
        # 退款统计
        pending_refunds = db.query(Refund).join(User).filter(
            Refund.status == "processing",
            non_admin_filter
        ).count()
        total_refund_amount = db.query(func.sum(Refund.amount)).join(User).filter(
            Refund.status == "completed",
            non_admin_filter
        ).scalar() or 0
        
        # 最近活动
        recent_orders = db.query(Order).join(User).filter(non_admin_filter).order_by(desc(Order.created_at)).limit(5).all()
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
        
        recent_refunds = db.query(Refund).join(User).filter(non_admin_filter).order_by(desc(Refund.created_at)).limit(3).all()
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


@router.get("/limits/metrics", dependencies=[Depends(admin_route())])
async def get_api_limit_metrics(
    current_admin: User = Depends(get_current_active_admin),
):
    """获取下游API并发限流状态（管理员专用）。"""
    try:
        metrics = []
        for api_name in settings.api_concurrency_limits.keys():
            m = await api_limiter.get_metrics(api_name)
            metrics.append(
                ApiLimitMetric(
                    api=m["api"],
                    limit=m["limit"],
                    active=m["active"],
                    available=m["available"],
                    leasedTokens=m["leased_tokens"],
                )
            )

        return SuccessResponse(
            data=ApiLimitMetricsResponse(metrics=metrics).dict(),
            message="获取并发限流指标成功",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
