from functools import wraps
from typing import Callable, Any, Union
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user, get_admin_user
from app.services.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()


def admin_required(func: Callable) -> Callable:
    """
    装饰器：要求用户必须是管理员
    用法: @admin_required
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 检查是否已经通过依赖注入获取了用户
        current_user = kwargs.get('current_user')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证信息",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def admin_route():
    """
    依赖函数：用于保护管理员路由
    用法: @router.get("/admin/users", dependencies=[Depends(admin_route())])
    """
    return get_admin_user


def admin_or_self_required(func: Callable) -> Callable:
    """
    装饰器：要求用户是管理员或访问自己的资源
    用法: @admin_or_self_required
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        target_user_id = kwargs.get('user_id')
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证信息",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查是否是管理员或访问自己的资源
        if not current_user.is_admin and str(current_user.user_id) != str(target_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能访问自己的资源或需要管理员权限"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


def permission_required(permission: str):
    """
    装饰器：要求用户具有特定权限（可扩展用于更细粒度的权限控制）
    用法: @permission_required("user_management")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供认证信息",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {permission}"
                )
            
            # 这里可以扩展更复杂的权限检查逻辑
            # 例如检查用户的具体权限列表
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class AdminAuthChecker:
    """管理员认证检查器类"""
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """检查用户是否是管理员"""
        return user.is_admin if user else False
    
    @staticmethod
    def check_admin_permission(user: User) -> None:
        """检查管理员权限，如果没有则抛出异常"""
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
    
    @staticmethod
    def check_admin_or_self(user: User, target_user_id: str) -> None:
        """检查管理员权限或访问自己的资源"""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未提供认证信息",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_admin and str(user.user_id) != str(target_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能访问自己的资源或需要管理员权限"
            )