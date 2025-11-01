from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

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


class OrderCreate(BaseModel):
    package_id: str
    payment_method: Optional[str] = None
    quantity: int = 1
    coupon_code: Optional[str] = None


@router.post("/orders")
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订单"""

    payment_service = PaymentService()

    try:
        order_info = await payment_service.create_order(
            db=db,
            user_id=current_user.id,
            package_id=order_data.package_id,
            payment_method=order_data.payment_method,
            coupon_code=order_data.coupon_code
        )

        return SuccessResponse(
            data=order_info,
            message="订单创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/aggregate/notify")
async def aggregate_notify(
    request: Request,
    db: Session = Depends(get_db),
):
    """聚合收银台异步通知"""

    payment_service = PaymentService()

    try:
        notify_data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"无法解析通知数据: {exc}") from exc

    success = await payment_service.handle_counter_notify(db, notify_data)

    return "SUCCESS" if success else "FAIL"


@router.get("/orders/{order_id}")
async def get_order_status(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单状态"""

    payment_service = PaymentService()

    try:
        order_status = await payment_service.get_order_status(db, order_id)

        # 检查订单是否属于当前用户
        if order_status.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="无权访问此订单")

        return SuccessResponse(
            data=order_status,
            message="获取订单状态成功"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消订单"""

    payment_service = PaymentService()

    try:
        success = await payment_service.cancel_order(db, order_id)

        if success:
            return SuccessResponse(
                data={"order_id": order_id},
                message="订单取消成功"
            )
        else:
            raise HTTPException(status_code=400, detail="订单取消失败")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
