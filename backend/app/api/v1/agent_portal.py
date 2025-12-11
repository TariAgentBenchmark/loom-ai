from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, desc, and_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.agent import Agent, AgentStatus, InvitationCode, InvitationCodeStatus
from app.models.user import User
from app.models.payment import Order, OrderStatus
from app.schemas.common import SuccessResponse
from app.api.v1.admin import _generate_invitation_code

router = APIRouter()


class ManagedAgentChild(BaseModel):
    id: int
    name: str
    level: int
    status: str
    parentAgentId: Optional[int]
    ownerUserId: Optional[str]
    ownerUserPhone: Optional[str]
    invitationCode: Optional[str]
    createdAt: Optional[str]


class ManagedAgentResponse(BaseModel):
    id: int
    name: str
    level: int
    status: str
    contact: Optional[str]
    notes: Optional[str]
    parentAgentId: Optional[int]
    ownerUserId: Optional[str]
    ownerUserPhone: Optional[str]
    invitationCode: Optional[str]
    createdAt: Optional[str]
    children: List[ManagedAgentChild]


class CreateChildAgentRequest(BaseModel):
    name: str = Field(..., max_length=100, description="二级代理商名称")
    userIdentifier: str = Field(..., description="绑定的已注册用户标识（userId/手机号/邮箱）")
    contact: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class AgentLedgerItem(BaseModel):
    orderId: str
    userId: str
    userPhone: Optional[str]
    paidAt: Optional[str]
    amount: int  # cents
    commission: int  # cents
    rate: float


class AgentLedgerResponse(BaseModel):
    items: List[AgentLedgerItem]
    totalAmount: int
    totalCommission: int
    totalOrders: int
    page: int
    pageSize: int
    totalPages: int


def _get_managed_agent(db: Session, current_user: User) -> Agent:
    agent = (
        db.query(Agent)
        .filter(Agent.owner_user_id == current_user.id, Agent.is_deleted.is_(False))
        .first()
    )
    if not agent:
        raise HTTPException(status_code=404, detail="当前账号未绑定代理商")
    return agent


def _compute_commission_cents(amount_cents: int, level: int) -> (int, float):
    """Calculate commission amount in cents and return applied rate."""
    amt = Decimal(amount_cents or 0)
    if amt <= 0:
        return 0, 0.0

    if level >= 2:
        rate = Decimal("0.06")
    else:
        # level 1 tiers: <10000 ->20%, >=10000 ->30% (units), amounts stored in cents
        threshold_cents = Decimal("10000") * 100
        rate = Decimal("0.20") if amt < threshold_cents else Decimal("0.30")

    commission = (amt * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(commission), float(rate)


@router.get("/me")
async def get_my_agent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户管理的代理商及下级代理"""
    agent = _get_managed_agent(db, current_user)

    child_agents = (
        db.query(Agent)
        .filter(Agent.parent_agent_id == agent.id, Agent.is_deleted.is_(False))
        .order_by(desc(Agent.created_at))
        .all()
    )

    related_agent_ids = [agent.id] + [child.id for child in child_agents]
    invitation_map = {}
    if related_agent_ids:
        codes = (
            db.query(InvitationCode)
            .filter(
                InvitationCode.agent_id.in_(related_agent_ids),
                InvitationCode.is_deleted.is_(False),
            )
            .order_by(desc(InvitationCode.created_at))
            .all()
        )
        for code in codes:
            invitation_map.setdefault(code.agent_id, code.code)

    owner_ids = [child.owner_user_id for child in child_agents if child.owner_user_id]
    owner_map = {
        user.id: user
        for user in db.query(User.id, User.user_id, User.phone)
        .filter(User.id.in_(owner_ids))
        .all()
    } if owner_ids else {}

    return SuccessResponse(
        data=ManagedAgentResponse(
            id=agent.id,
            name=agent.name,
            level=agent.level or 1,
            status=agent.status.value if agent.status else AgentStatus.ACTIVE.value,
            contact=agent.contact,
            notes=agent.notes,
            parentAgentId=agent.parent_agent_id,
            ownerUserId=current_user.user_id,
            ownerUserPhone=current_user.phone,
            invitationCode=invitation_map.get(agent.id),
            createdAt=agent.created_at.isoformat() if agent.created_at else None,
            children=[
                ManagedAgentChild(
                    id=child.id,
                    name=child.name,
                    level=child.level or 2,
                    status=child.status.value if child.status else AgentStatus.ACTIVE.value,
                    parentAgentId=child.parent_agent_id,
                    ownerUserId=owner_map.get(child.owner_user_id).user_id if child.owner_user_id and child.owner_user_id in owner_map else None,
                    ownerUserPhone=owner_map.get(child.owner_user_id).phone if child.owner_user_id and child.owner_user_id in owner_map else None,
                    invitationCode=invitation_map.get(child.id),
                    createdAt=child.created_at.isoformat() if child.created_at else None,
                )
                for child in child_agents
            ],
        ).dict(),
        message="获取代理商信息成功",
    )


@router.post("/agents")
async def create_child_agent(
    payload: CreateChildAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建二级代理商，限一级代理用户使用"""
    parent_agent = _get_managed_agent(db, current_user)
    parent_level = parent_agent.level or 1
    if parent_level >= 2:
        raise HTTPException(status_code=403, detail="仅一级代理商可以创建下级")
    if parent_agent.status != AgentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="当前代理商未启用，无法创建下级")

    duplicate = (
        db.query(Agent)
        .filter(Agent.name == payload.name, Agent.is_deleted.is_(False))
        .first()
    )
    if duplicate:
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

    child_agent = Agent(
        name=payload.name,
        owner_user_id=owner_user.id,
        parent_agent_id=parent_agent.id,
        level=min(parent_level + 1, 2),
        contact=payload.contact,
        notes=payload.notes,
        status=AgentStatus.ACTIVE,
    )
    db.add(child_agent)
    db.flush()

    invite = InvitationCode(
        code=_generate_invitation_code(),
        agent_id=child_agent.id,
        status=InvitationCodeStatus.ACTIVE,
    )
    db.add(invite)

    db.commit()
    db.refresh(child_agent)
    db.refresh(invite)

    return SuccessResponse(
        data=ManagedAgentChild(
            id=child_agent.id,
            name=child_agent.name,
            level=child_agent.level or 2,
            status=child_agent.status.value if child_agent.status else AgentStatus.ACTIVE.value,
            parentAgentId=child_agent.parent_agent_id,
            ownerUserId=owner_user.user_id,
            ownerUserPhone=owner_user.phone,
            invitationCode=invite.code,
            createdAt=child_agent.created_at.isoformat() if child_agent.created_at else None,
        ).dict(),
        message="二级代理商创建成功",
    )


@router.get("/users/search")
async def search_users_for_agent(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """代理商创建下级时搜索已注册用户"""
    agent = _get_managed_agent(db, current_user)
    if agent.level and agent.level > 2:
        raise HTTPException(status_code=403, detail="无权限")

    keyword = q.strip()
    if not keyword:
        return SuccessResponse(data={"users": []}, message="用户搜索成功")

    digits_only = "".join(ch for ch in keyword if ch.isdigit())
    users = (
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
        .limit(min(max(limit, 1), 50))
        .all()
    )

    return SuccessResponse(
        data={
            "users": [
                {
                    "userId": user.user_id,
                    "phone": user.phone,
                    "email": user.email,
                    "nickname": user.nickname,
                }
                for user in users
            ]
        },
        message="用户搜索成功",
    )


@router.get("/ledger")
async def get_agent_ledger(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: int = 1,
    pageSize: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """代理商佣金流水"""
    agent = _get_managed_agent(db, current_user)
    page = max(page, 1)
    pageSize = min(max(pageSize, 1), 100)

    start_dt = datetime.fromisoformat(startDate) if startDate else None
    end_dt = datetime.fromisoformat(endDate) if endDate else None

    query = (
        db.query(Order, User)
        .join(User, User.id == Order.user_id)
        .filter(
            Order.status == OrderStatus.PAID.value,
            User.agent_id == agent.id,
        )
    )
    if start_dt:
        query = query.filter(Order.paid_at >= start_dt)
    if end_dt:
        query = query.filter(Order.paid_at <= end_dt)

    total_orders = query.count()
    total_pages = (total_orders + pageSize - 1) // pageSize

    rows = (
        query.order_by(desc(Order.paid_at))
        .offset((page - 1) * pageSize)
        .limit(pageSize)
        .all()
    )

    items: List[AgentLedgerItem] = []
    total_amount = 0
    total_commission = 0
    for order, user in rows:
        amount = order.final_amount or 0
        commission, rate = _compute_commission_cents(amount, agent.level or 1)
        total_amount += amount
        total_commission += commission
        items.append(
            AgentLedgerItem(
                orderId=order.order_id,
                userId=user.user_id,
                userPhone=user.phone,
                paidAt=order.paid_at.isoformat() if order.paid_at else None,
                amount=amount,
                commission=commission,
                rate=rate,
            )
        )

    # recompute totals over full set for accuracy
    full_amount = 0
    full_commission = 0
    for order_obj, _ in query.all():
        amt = order_obj.final_amount or 0
        com, _ = _compute_commission_cents(amt, agent.level or 1)
        full_amount += amt
        full_commission += com

    return SuccessResponse(
        data=AgentLedgerResponse(
            items=items,
            totalAmount=full_amount,
            totalCommission=full_commission,
            totalOrders=total_orders,
            page=page,
            pageSize=pageSize,
            totalPages=total_pages,
        ).dict(),
        message="获取佣金流水成功",
    )
