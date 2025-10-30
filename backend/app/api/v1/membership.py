"""会员API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.membership_service import MembershipService
from app.services.credit_math import to_float

router = APIRouter()


@router.get("/packages", response_model=List[Dict[str, Any]])
async def get_packages(
    category: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取套餐列表"""
    service = MembershipService()
    packages = await service.get_all_packages(db, category)
    return packages


@router.get("/public/packages", response_model=List[Dict[str, Any]])
async def get_public_packages(
    category: str = None,
    db: Session = Depends(get_db)
):
    """获取公开套餐列表（无需认证）"""
    service = MembershipService()
    packages = await service.get_all_packages(db, category)
    return packages


@router.get("/services", response_model=List[Dict[str, Any]])
async def get_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取服务价格列表"""
    service = MembershipService()
    services = await service.get_service_prices(db)
    return services


@router.post("/purchase")
async def purchase_package(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """购买套餐"""
    package_id = request.get("package_id")
    payment_method = request.get("payment_method", "alipay")
    order_id = request.get("order_id")

    if not package_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少套餐ID"
        )

    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少订单ID"
        )

    service = MembershipService()
    try:
        result = await service.purchase_package(
            db=db,
            user_id=current_user.id,
            package_id=package_id,
            payment_method=payment_method,
            order_id=order_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refund")
async def refund_package(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """退款套餐"""
    user_membership_id = request.get("user_membership_id")
    reason = request.get("reason", "用户申请退款")

    if not user_membership_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少会员记录ID"
        )

    service = MembershipService()
    try:
        result = await service.refund_package(
            db=db,
            user_id=current_user.id,
            user_membership_id=user_membership_id,
            reason=reason
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/new-user-bonus")
async def apply_new_user_bonus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """申请新用户福利"""
    service = MembershipService()
    result = await service.apply_new_user_bonus(db, current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )

    return result


@router.get("/my-memberships", response_model=List[Dict[str, Any]])
async def get_my_memberships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取我的会员记录"""
    service = MembershipService()
    memberships = await service.get_user_memberships(db, current_user.id)
    return memberships


@router.get("/service-cost")
async def get_service_cost(
    service_key: str,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取服务成本"""
    service = MembershipService()
    cost = await service.calculate_service_cost(db, service_key, quantity)

    if cost is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务不存在"
        )

    return {
        "service_key": service_key,
        "quantity": quantity,
        "total_cost": to_float(cost),
        "unit_cost": to_float(cost / quantity) if quantity > 0 else 0
    }


@router.get("/can-afford-service")
async def can_afford_service(
    service_key: str,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查是否能支付服务费用"""
    service = MembershipService()
    can_afford = await service.can_afford_service(db, current_user.id, service_key, quantity)

    cost = await service.calculate_service_cost(db, service_key, quantity)

    return {
        "can_afford": can_afford,
        "service_key": service_key,
        "quantity": quantity,
        "required_credits": to_float(cost) if cost is not None else None,
        "current_credits": to_float(current_user.credits)
    }


@router.post("/initialize-packages")
async def initialize_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """初始化套餐数据（管理员专用）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    service = MembershipService()
    await service.initialize_packages(db)

    return {"message": "套餐数据初始化成功"}