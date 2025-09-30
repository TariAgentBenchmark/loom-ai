from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse

router = APIRouter()


@router.get("/packages")
async def get_packages(type: Optional[str] = None):
    """获取套餐列表"""
    
    # 模拟套餐数据（实际应该从数据库获取）
    packages_data = {
        "membership": {
            "monthly": [
                {
                    "packageId": "monthly_trial",
                    "name": "试用体验",
                    "type": "monthly",
                    "price": 0,
                    "originalPrice": 0,
                    "credits": 200,
                    "duration": 7,
                    "features": [
                        "赠送200算力积分",
                        "7天内有效",
                        "循环图案处理",
                        "定位花提取",
                        "高清放大",
                        "毛线刺绣增强"
                    ],
                    "popular": False
                },
                {
                    "packageId": "monthly_light",
                    "name": "轻享版",
                    "type": "monthly", 
                    "price": 2900,
                    "originalPrice": 4900,
                    "credits": 3000,
                    "duration": 30,
                    "features": [
                        "每月3000算力积分",
                        "AI应用高速队列",
                        "所有基础功能"
                    ],
                    "popular": True,
                    "discount": "限时优惠"
                }
            ]
        },
        "credits": [
            {
                "packageId": "credits_basic",
                "name": "基础算力包",
                "type": "credits",
                "price": 1900,
                "credits": 1000,
                "description": "适合偶尔使用",
                "popular": False
            }
        ]
    }
    
    return SuccessResponse(
        data=packages_data,
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
    # 这里应该实现完整的订单创建逻辑
    # 暂时返回模拟响应
    
    import uuid
    from datetime import datetime, timedelta
    
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    
    return SuccessResponse(
        data={
            "orderId": order_id,
            "packageId": order_data.package_id,
            "packageName": "基础版",
            "originalAmount": 8900,
            "discountAmount": 2000,
            "finalAmount": 6900,
            "paymentMethod": order_data.payment_method,
            "status": "pending",
            "paymentUrl": f"https://pay.loom-ai.com/pay/{order_id}",
            "qrCode": f"https://api.loom-ai.com/payment/qr/{order_id}.png",
            "expiresAt": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "createdAt": datetime.utcnow().isoformat()
        },
        message="订单创建成功"
    )
