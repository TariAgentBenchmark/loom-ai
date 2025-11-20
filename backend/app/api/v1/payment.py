from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.services.payment_service import PaymentService

router = APIRouter()


@router.get("/packages")
async def get_packages(
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取套餐列表"""

    from app.services.membership_service import MembershipService

    membership_service = MembershipService()
    packages = await membership_service.get_all_packages(db, type)

    return SuccessResponse(
        data=packages,
        message="获取套餐列表成功"
    )


class CreateCounterOrderRequest(BaseModel):
    """Request model for creating counter payment order."""

    out_order_no: str
    total_amount: int
    order_info: str
    notify_url: Optional[str] = None
    callback_url: Optional[str] = None
    payment_method: Optional[str] = "ALIPAY"
    vpos_id: Optional[str] = None
    channel_id: Optional[str] = None
    order_efficient_time: Optional[str] = None
    support_cancel: Optional[int] = 0
    support_refund: Optional[int] = 1
    support_repeat_pay: Optional[int] = 1


class QueryOrderRequest(BaseModel):
    """Request model for querying order status."""

    out_order_no: str


class CloseOrderRequest(BaseModel):
    """Request model for closing order."""

    out_order_no: str


@router.post("/lakala/counter/create")
async def create_counter_order(
    payload: CreateCounterOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """Create payment order in Lakala Aggregated Payment Gateway."""

    payment_service = PaymentService()

    try:
        result = await payment_service.create_lakala_counter_order(
            out_order_no=payload.out_order_no,
            total_amount=payload.total_amount,
            order_info=payload.order_info,
            notify_url=payload.notify_url,
            callback_url=payload.callback_url,
            payment_method=payload.payment_method,
            vpos_id=payload.vpos_id,
            channel_id=payload.channel_id,
            order_efficient_time=payload.order_efficient_time,
            support_cancel=payload.support_cancel,
            support_refund=payload.support_refund,
            support_repeat_pay=payload.support_repeat_pay,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SuccessResponse(
        data=result,
        message="聚合收银台订单创建成功",
    )


@router.post("/lakala/counter/query")
async def query_counter_order(
    payload: QueryOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """Query payment order status."""

    payment_service = PaymentService()

    try:
        result = await payment_service.query_lakala_order_status(payload.out_order_no)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SuccessResponse(
        data=result,
        message="订单状态查询成功",
    )


@router.post("/lakala/counter/close")
async def close_counter_order(
    payload: CloseOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """Close payment order."""

    payment_service = PaymentService()

    try:
        result = await payment_service.close_lakala_order(payload.out_order_no)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SuccessResponse(
        data=result,
        message="订单关闭成功",
    )
