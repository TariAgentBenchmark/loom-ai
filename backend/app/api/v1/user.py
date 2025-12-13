from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.services.credit_math import to_float

router = APIRouter()


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """获取用户信息"""
    return SuccessResponse(
        data={
            "userId": current_user.user_id,
            "email": current_user.email,
            "nickname": current_user.nickname,
            "phone": current_user.phone,
            "avatar": current_user.avatar_url,
            "credits": to_float(current_user.credits),
            "membershipType": current_user.membership_type.value,
            "membershipExpiry": current_user.membership_expiry,
            "totalProcessed": current_user.total_processed,
            "monthlyProcessed": current_user.monthly_processed,
            "joinedAt": current_user.created_at,
            "lastLoginAt": current_user.last_login_at,
            "status": current_user.status.value,
            "isAdmin": current_user.is_admin,
            "isTestUser": getattr(current_user, "is_test_user", False),
            "agentId": current_user.agent_id,
            "managedAgentId": current_user.managed_agent.id if current_user.managed_agent else None,
            "managedAgentLevel": current_user.managed_agent.level if current_user.managed_agent else None,
            "managedAgentName": current_user.managed_agent.name if current_user.managed_agent else None,
            "managedAgentStatus": current_user.managed_agent.status.value if current_user.managed_agent else None,
        },
        message="获取用户信息成功"
    )


@router.put("/profile")
async def update_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    try:
        if user_data.nickname:
            current_user.nickname = user_data.nickname
        
        if user_data.phone:
            current_user.phone = user_data.phone
        
        db.commit()
        db.refresh(current_user)
        
        return SuccessResponse(
            data={
                "userId": current_user.user_id,
                "email": current_user.email,
                "nickname": current_user.nickname,
                "phone": current_user.phone,
                "updatedAt": current_user.updated_at
            },
            message="用户信息更新成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
