import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.credit import CreditTransaction, CreditSource
from app.models.payment import Order, OrderStatus, PaymentMethod, PackageType
from app.models.membership_package import MembershipPackage, PackageCategory
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.services.payment_service import PaymentService
from app.services.lakala_api import LakalaApiClient, LakalaAPIError
from app.services.membership_service import MembershipService
from app.services.credit_math import to_decimal
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


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
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Create payment order in Lakala Aggregated Payment Gateway."""

    payment_service = PaymentService()
    membership_service = MembershipService()

    try:
        # 测试用户直接完成购买，不跳转支付
        if getattr(current_user, "is_test_user", False):
            _ensure_local_order_record(db=db, user=current_user, payload=payload)
            package_id = _parse_package_id(payload.out_order_no)
            if package_id:
                await membership_service.purchase_package(
                    db=db,
                    user_id=current_user.id,
                    package_id=package_id,
                    payment_method="test",
                    order_id=payload.out_order_no,
                )
            order = (
                db.query(Order)
                .filter(Order.order_id == payload.out_order_no)
                .order_by(Order.id.desc())
                .first()
            )
            if order:
                order.status = OrderStatus.PAID.value
                order.paid_at = datetime.utcnow()
                order.transaction_id = "TEST-PAID"
                if order.agent_id_snapshot is None:
                    order.agent_id_snapshot = current_user.agent_id
                meta = order.extra_metadata or {}
                meta["test_user"] = True
                order.extra_metadata = meta
                db.commit()

            return SuccessResponse(
                data={
                    "orderId": payload.out_order_no,
                    "paymentSkipped": True,
                    "message": "测试用户已直接完成充值，无需支付",
                },
                message="测试用户已完成支付",
            )

        notify_url = (
            payload.notify_url
            or f"{settings.base_url.rstrip('/')}/api/v1/payment/lakala/counter/notify"
        )
        # 兼容旧前端的路径，强制改到新回调地址
        if "/api/payment/notify" in notify_url:
            notify_url = notify_url.replace(
                "/api/payment/notify", "/api/v1/payment/lakala/counter/notify"
            )
        callback_url = payload.callback_url or f"{settings.base_url.rstrip('/')}/payment/success"

        result = await payment_service.create_lakala_counter_order(
            out_order_no=payload.out_order_no,
            total_amount=payload.total_amount,
            order_info=payload.order_info,
            notify_url=notify_url,
            callback_url=callback_url,
            payment_method=payload.payment_method,
            vpos_id=payload.vpos_id,
            channel_id=payload.channel_id,
            order_efficient_time=payload.order_efficient_time,
            support_cancel=payload.support_cancel,
            support_refund=payload.support_refund,
            support_repeat_pay=payload.support_repeat_pay,
        )

        _ensure_local_order_record(
            db=db,
            user=current_user,
            payload=payload,
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


@router.post("/lakala/counter/notify")
async def lakala_counter_notify(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Lakala asynchronous counter payment notifications."""

    raw_body = await request.body()
    body_text = raw_body.decode("utf-8")

    timestamp = request.headers.get("Lklapi-Timestamp")
    nonce = request.headers.get("Lklapi-Nonce")
    signature = request.headers.get("Lklapi-Signature")

    headers_present = all([timestamp, nonce, signature])
    if not headers_present and not settings.lakala_skip_signature_verification:
        logger.warning(
            "Missing Lakala notify headers, continue processing with relaxed verification. "
            "timestamp=%s nonce=%s signature_present=%s body=%s",
            timestamp,
            nonce,
            bool(signature),
            body_text,
        )

    if headers_present:
        client = LakalaApiClient()
        if not client.verify_async_notify(
            timestamp=timestamp,
            nonce=nonce,
            body=body_text,
            signature=signature,
        ):
            logger.error(
                "Lakala notify signature verification failed. headers=%s body=%s",
                dict(request.headers),
                body_text,
            )
            if not settings.lakala_skip_signature_verification:
                logger.warning(
                    "Proceeding despite signature verification failure (relaxed mode). "
                    "Set LAKALA_SKIP_SIGNATURE_VERIFICATION=true to suppress this log."
                )
            else:
                logger.warning("Skipping Lakala notify signature verification failure due to config.")
    else:
        logger.warning(
            "Skipping Lakala notify signature verification because headers are missing and skip flag is enabled. body=%s",
            body_text,
        )

    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        logger.error("Invalid Lakala notify JSON: %s error=%s", body_text, exc)
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    logger.info("Received Lakala notify: %s", payload)

    notify_data = payload.get("resp_data") or payload.get("respData") or payload
    out_order_no = (
        notify_data.get("out_order_no")
        or notify_data.get("outOrderNo")
        or notify_data.get("order_no")
        or notify_data.get("orderNo")
    )
    pay_order_no = notify_data.get("pay_order_no") or notify_data.get("payOrderNo")

    if not out_order_no:
        logger.error("Lakala notify missing out_order_no: %s", notify_data)
        return {"code": "FAIL", "msg": "missing out_order_no"}

    order: Order | None = (
        db.query(Order).filter(Order.order_id == out_order_no).order_by(Order.id.desc()).first()
    )
    if not order:
        logger.error("Lakala notify for unknown order: %s", out_order_no)
        return {"code": "FAIL", "msg": "order not found"}

    if order.status == OrderStatus.PAID.value:
        return {"code": "SUCCESS", "msg": "already processed"}

    # 完成积分入账
    membership_service = MembershipService()
    try:
        await membership_service.purchase_package(
            db=db,
            user_id=order.user_id,
            package_id=order.package_id,
            payment_method=PaymentMethod.LAKALA_COUNTER.value,
            order_id=order.order_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to credit order %s via purchase_package: %s", out_order_no, exc)

        # Fallback: 若套餐信息缺失但订单含有积分数，则直接入账积分
        fallback_credits = order.credits_amount
        if fallback_credits and fallback_credits > 0:
            try:
                user = db.query(User).filter(User.id == order.user_id).first()
                if not user:
                    raise Exception("user not found for fallback crediting")

                user.add_credits(to_decimal(fallback_credits))
                transaction = CreditTransaction(
                    transaction_id=f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                    user_id=user.id,
                    type="earn",
                    amount=to_decimal(fallback_credits),
                    balance_after=to_decimal(user.credits or 0),
                    source=CreditSource.PURCHASE.value,
                    description=f"购买 {order.package_name or order.package_id or '套餐'} (补记)",
                    related_order_id=order.order_id,
                )
                db.add(transaction)
                db.commit()
                logger.info(
                    "Fallback credited %s credits for order %s after purchase_package failure",
                    fallback_credits,
                    out_order_no,
                )
            except Exception as inner_exc:  # noqa: BLE001
                logger.error(
                    "Fallback crediting failed for order %s: %s", out_order_no, inner_exc
                )
                return {"code": "FAIL", "msg": "credit failed"}
        else:
            return {"code": "FAIL", "msg": "credit failed"}

    order.status = OrderStatus.PAID.value
    order.transaction_id = pay_order_no or order.transaction_id
    order.paid_at = datetime.utcnow()
    if order.agent_id_snapshot is None:
        user = db.query(User).filter(User.id == order.user_id).first()
        order.agent_id_snapshot = user.agent_id if user else None
    meta = order.extra_metadata or {}
    meta["lakala_notify"] = notify_data
    order.extra_metadata = meta
    db.commit()

    return {"code": "SUCCESS", "msg": "ok"}


def _parse_package_id(out_order_no: str) -> Optional[str]:
    parts = out_order_no.split("_")
    if len(parts) <= 1:
        return None
    # 支付单号格式: <prefix>_<package_id>，而 package_id 可能包含下划线
    return "_".join(parts[1:])


def _ensure_local_order_record(
    *,
    db: Session,
    user: User,
    payload: CreateCounterOrderRequest,
) -> None:
    package_id = _parse_package_id(payload.out_order_no) or ""
    package: MembershipPackage | None = None
    if package_id:
        package = (
            db.query(MembershipPackage)
            .filter(MembershipPackage.package_id == package_id)
            .first()
        )

    # 根据套餐类别确定订单类型与积分
    package_type = PackageType.MEMBERSHIP.value
    package_credits: int | None = None
    if package:
        if package.category == PackageCategory.DISCOUNT.value:
            package_type = PackageType.CREDITS.value
            package_credits = package.total_credits
        else:
            package_type = PackageType.MEMBERSHIP.value

    order = db.query(Order).filter(Order.order_id == payload.out_order_no).first()
    if order:
        order.original_amount = payload.total_amount
        order.final_amount = payload.total_amount
        if not order.package_name:
            order.package_name = payload.order_info
        if not order.expires_at:
            order.expires_at = datetime.utcnow() + timedelta(minutes=5)
        if not order.payment_method:
            order.payment_method = PaymentMethod.LAKALA_COUNTER.value
        if not order.package_type:
            order.package_type = package_type
        if not order.credits_amount and package_credits:
            order.credits_amount = package_credits
    else:
        order = Order(
            order_id=payload.out_order_no,
            user_id=user.id,
            package_id=(package.package_id if package else package_id),
            package_name=package.name if package else payload.order_info,
            package_type=package_type,
            original_amount=payload.total_amount,
            final_amount=payload.total_amount,
            payment_method=PaymentMethod.LAKALA_COUNTER.value,
            status=OrderStatus.PENDING.value,
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            credits_amount=package_credits,
            extra_metadata={
                "payment_method": PaymentMethod.LAKALA_COUNTER.value,
                "total_amount": payload.total_amount,
            },
        )
        db.add(order)

    db.commit()
