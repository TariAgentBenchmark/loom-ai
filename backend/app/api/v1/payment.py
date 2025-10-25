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
    payment_method: str
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


@router.post("/wechat/notify")
async def wechat_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    """微信支付回调"""

    payment_service = PaymentService()

    try:
        # 解析XML数据
        body = await request.body()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(body.decode('utf-8'))

        notify_data = {}
        for child in root:
            notify_data[child.tag] = child.text

        # 处理回调
        success = await payment_service.handle_wechat_notify(db, notify_data)

        if success:
            return {
                "return_code": "SUCCESS",
                "return_msg": "OK"
            }
        else:
            return {
                "return_code": "FAIL",
                "return_msg": "处理失败"
            }

    except Exception as e:
        return {
            "return_code": "FAIL",
            "return_msg": str(e)
        }


@router.post("/alipay/notify")
async def alipay_notify(
    request: Request,
    db: Session = Depends(get_db)
):
    """支付宝支付回调"""

    payment_service = PaymentService()

    try:
        # 解析表单数据
        form_data = await request.form()
        notify_data = dict(form_data)

        # 处理回调
        success = await payment_service.handle_alipay_notify(db, notify_data)

        if success:
            return "success"
        else:
            return "failure"

    except Exception as e:
        return "failure"


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
        if order_status["user_id"] != current_user.id:
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
