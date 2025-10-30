from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证token
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # 获取用户
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise credentials_exception
        
        # 检查用户状态
        if user.status.value != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账户已被暂停"
            )
        
        # 验证管理员会话（如果token中包含admin_session标记）
        is_admin_session = payload.get("admin_session", False)
        if is_admin_session and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无效的管理员会话"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.status.value == "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    return current_user


async def get_premium_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取付费会员用户"""
    if not current_user.is_premium_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要付费会员权限"
        )
    return current_user


async def check_credits(
    required_credits: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """检查用户积分是否足够"""
    if not current_user.can_afford(required_credits):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"积分不足，需要{required_credits}积分"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_active_admin(
    current_user: User = Depends(get_admin_user)
) -> User:
    """获取当前活跃管理员用户"""
    if not current_user.status.value == "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员账户未激活"
        )
    return current_user
