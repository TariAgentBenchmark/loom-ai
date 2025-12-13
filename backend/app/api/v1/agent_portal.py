from typing import List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.agent import Agent, AgentStatus, InvitationCode
from app.models.user import User
from app.models.payment import Order, OrderStatus
from app.models.agent_commission import AgentCommission, AgentCommissionStatus
from app.schemas.common import SuccessResponse

router = APIRouter()


class ManagedAgentResponse(BaseModel):
    id: int
    name: str
    status: str
    contact: Optional[str]
    notes: Optional[str]
    ownerUserId: Optional[str]
    ownerUserPhone: Optional[str]
    invitationCode: Optional[str]
    createdAt: Optional[str]


class AgentLedgerItem(BaseModel):
    orderId: str
    userId: str
    userPhone: Optional[str]
    paidAt: Optional[str]
    amount: int  # cents
    commission: int  # cents
    rate: float
    status: str
    settledAt: Optional[str] = None


class AgentLedgerResponse(BaseModel):
    items: List[AgentLedgerItem]
    totalAmount: int
    totalCommission: int
    totalOrders: int
    settledAmount: int
    unsettledAmount: int
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


def _compute_commission_cents(amount_cents: int) -> (int, float):
    """Calculate commission amount in cents based on tiered rule."""
    amt = Decimal(amount_cents or 0)
    if amt <= 0:
        return 0, 0.0

    threshold_cents = Decimal("30000") * 100  # 3万
    lower_part = min(amt, threshold_cents)
    higher_part = max(amt - threshold_cents, 0)
    commission = lower_part * Decimal("0.20") + higher_part * Decimal("0.25")
    commission = commission.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # effective rate for display
    effective_rate = float((commission / amt).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    return int(commission), effective_rate


def _compute_commission_running_total(order_rows: list) -> dict:
    """按代理累计充值计算佣金，前 30000 部分 20%，超过部分 25%"""
    threshold_cents = Decimal("30000") * 100
    cumulative = Decimal("0")
    result = {}

    def _order_key(order: Order):
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


@router.get("/me")
async def get_my_agent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户管理的代理商"""
    agent = _get_managed_agent(db, current_user)
    related_agent_ids = [agent.id]
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

    return SuccessResponse(
        data=ManagedAgentResponse(
            id=agent.id,
            name=agent.name,
            status=agent.status.value if agent.status else AgentStatus.ACTIVE.value,
            contact=agent.contact,
            notes=agent.notes,
            ownerUserId=current_user.user_id,
            ownerUserPhone=current_user.phone,
            invitationCode=invitation_map.get(agent.id),
            createdAt=agent.created_at.isoformat() if agent.created_at else None,
        ).dict(),
        message="获取代理商信息成功",
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

    base_query = (
        db.query(Order, User)
        .join(User, User.id == Order.user_id)
        .filter(
            Order.status == OrderStatus.PAID.value,
            User.agent_id == agent.id,
        )
    )
    if start_dt:
        base_query = base_query.filter(Order.paid_at >= start_dt)
    if end_dt:
        base_query = base_query.filter(Order.paid_at <= end_dt)

    all_rows = base_query.order_by(desc(Order.paid_at)).all()
    total_orders = len(all_rows)
    total_pages = (total_orders + pageSize - 1) // pageSize

    computed_map = _compute_commission_running_total(all_rows)

    # 全量订单对应的结算记录
    order_ids = [o.id for o, _u in all_rows]
    commission_map = {}
    if order_ids:
        records = (
            db.query(AgentCommission)
            .filter(AgentCommission.agent_id == agent.id, AgentCommission.order_id.in_(order_ids))
            .all()
        )
        commission_map = {rec.order_id: rec for rec in records}

    full_amount = 0
    full_commission = 0
    settled_total = 0
    for order_obj, _ in all_rows:
        amt = order_obj.final_amount or 0
        computed = computed_map.get(order_obj.id, {"commission": 0, "rate": 0.0})
        com_amount = int(computed["commission"])
        record = commission_map.get(order_obj.id)
        if record and record.status == AgentCommissionStatus.SETTLED and record.amount is not None:
            com_amount = int(record.amount)
            settled_total += int(record.amount)
        full_amount += amt
        full_commission += com_amount

    unsettled_total = max(full_commission - settled_total, 0)

    start_idx = (page - 1) * pageSize
    end_idx = start_idx + pageSize
    page_rows = all_rows[start_idx:end_idx]

    items: List[AgentLedgerItem] = []
    for order, user in page_rows:
        amount = order.final_amount or 0
        record = commission_map.get(order.id)
        computed = computed_map.get(order.id, {"commission": 0, "rate": 0.0})
        commission = int(computed["commission"])
        rate = float(computed["rate"])
        status = AgentCommissionStatus.UNSETTLED
        settled_at = None
        if record:
            status = record.status
            settled_at = record.settled_at.isoformat() if record.settled_at else None
            if record.amount is not None:
                commission = int(record.amount)
            if record.rate is not None:
                rate = float(record.rate)

        items.append(
            AgentLedgerItem(
                orderId=order.order_id,
                userId=user.user_id,
                userPhone=user.phone,
                paidAt=order.paid_at.isoformat() if order.paid_at else None,
                amount=amount,
                commission=commission,
                rate=rate,
                status=status,
                settledAt=settled_at,
            )
        )

    return SuccessResponse(
        data=AgentLedgerResponse(
            items=items,
            totalAmount=full_amount,
            totalCommission=full_commission,
            totalOrders=total_orders,
            settledAmount=settled_total,
            unsettledAmount=unsettled_total,
            page=page,
            pageSize=pageSize,
            totalPages=total_pages,
        ).dict(),
        message="获取佣金流水成功",
    )
