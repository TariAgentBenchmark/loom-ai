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


class LakalaMicropayRequest(BaseModel):
    """Generic wrapper for Lakala Micropay req_data payload."""

    req_data: Dict[str, Any]


@router.post("/lakala/micropay")
async def lakala_micropay(
    payload: LakalaMicropayRequest,
    current_user: User = Depends(get_current_user),
):
    """Call the Lakala Micropay API with the provided req_data structure."""

    payment_service = PaymentService()

    try:
        result = await payment_service.create_lakala_micropay(payload.req_data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SuccessResponse(
        data=result,
        message="拉卡拉 Micropay 请求成功",
    )
