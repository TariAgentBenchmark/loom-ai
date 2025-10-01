from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.auth_service import AuthService
from app.schemas.common import SuccessResponse

router = APIRouter()
auth_service = AuthService()
security = HTTPBearer()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    nickname: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordReset(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class ForgotPassword(BaseModel):
    email: EmailStr


@router.post("/register")
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        # 验证密码
        if user_data.password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="密码确认不一致")
        
        if len(user_data.password) < 8:
            raise HTTPException(status_code=400, detail="密码长度至少8位")
        
        # 注册用户
        user = await auth_service.register_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            nickname=user_data.nickname,
            phone=user_data.phone
        )
        
        return SuccessResponse(
            data={
                "userId": user.user_id,
                "email": user.email,
                "nickname": user.nickname,
                "credits": user.credits,
                "createdAt": user.created_at
            },
            message="注册成功，已赠送200算力"
        )
        
    except Exception as e:
        if "邮箱已存在" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        user = await auth_service.authenticate_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        # 创建令牌
        tokens = auth_service.create_login_tokens(user)
        
        return SuccessResponse(
            data={
                "accessToken": tokens["access_token"],
                "refreshToken": tokens["refresh_token"],
                "expiresIn": tokens["expires_in"],
                "tokenType": tokens["token_type"],
                "user": {
                    "userId": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "credits": user.credits,
                    "avatar": user.avatar_url
                }
            },
            message="登录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/login")
async def admin_login(
    admin_data: AdminLogin,
    db: Session = Depends(get_db)
):
    """管理员登录"""
    try:
        user = await auth_service.authenticate_admin(
            db=db,
            email=admin_data.email,
            password=admin_data.password
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        
        # 创建管理员令牌
        tokens = auth_service.create_admin_login_tokens(user)
        
        return SuccessResponse(
            data={
                "accessToken": tokens["access_token"],
                "refreshToken": tokens["refresh_token"],
                "expiresIn": tokens["expires_in"],
                "tokenType": tokens["token_type"],
                "isAdmin": tokens["is_admin"],
                "adminSession": tokens["admin_session"],
                "user": {
                    "userId": user.user_id,
                    "email": user.email,
                    "nickname": user.nickname,
                    "credits": user.credits,
                    "avatar": user.avatar_url,
                    "isAdmin": user.is_admin
                }
            },
            message="管理员登录成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if "非管理员账户" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """刷新令牌"""
    try:
        # 验证refresh token
        payload = auth_service.verify_token(credentials.credentials, "refresh")
        if not payload:
            raise HTTPException(status_code=401, detail="无效的刷新令牌")
        
        # 获取用户
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        
        # 创建新的访问令牌
        access_token = auth_service.create_access_token(
            data={"sub": user.user_id, "email": user.email}
        )
        
        return SuccessResponse(
            data={
                "accessToken": access_token,
                "expiresIn": auth_service.access_token_expire_minutes * 60,
                "tokenType": "bearer"
            },
            message="Token刷新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """用户登出"""
    # 在实际应用中，可以将token加入黑名单
    # 这里简单返回成功响应
    return SuccessResponse(
        data=None,
        message="登出成功"
    )


@router.post("/forgot-password")
async def forgot_password(
    request_data: ForgotPassword,
    db: Session = Depends(get_db)
):
    """忘记密码"""
    try:
        reset_token = await auth_service.request_password_reset(
            db=db,
            email=request_data.email
        )
        
        if not reset_token:
            # 为了安全，即使邮箱不存在也返回成功
            return SuccessResponse(
                data={"message": "如果邮箱存在，重置邮件已发送"},
                message="密码重置邮件已发送"
            )
        
        # TODO: 发送重置邮件
        # await send_reset_email(request_data.email, reset_token)
        
        return SuccessResponse(
            data={
                "resetToken": reset_token,  # 开发环境返回，生产环境不应返回
                "expiresIn": 3600
            },
            message="密码重置邮件已发送"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        if reset_data.new_password != reset_data.confirm_password:
            raise HTTPException(status_code=400, detail="密码确认不一致")
        
        if len(reset_data.new_password) < 8:
            raise HTTPException(status_code=400, detail="密码长度至少8位")
        
        success = await auth_service.reset_password(
            db=db,
            reset_token=reset_data.reset_token,
            new_password=reset_data.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="重置令牌无效或已过期")
        
        return SuccessResponse(
            data=None,
            message="密码重置成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    try:
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(status_code=400, detail="密码确认不一致")
        
        if len(password_data.new_password) < 8:
            raise HTTPException(status_code=400, detail="密码长度至少8位")
        
        success = await auth_service.change_password(
            db=db,
            user=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="当前密码错误")
        
        return SuccessResponse(
            data=None,
            message="密码修改成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify")
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """验证Token"""
    return SuccessResponse(
        data={
            "valid": True,
            "user": {
                "userId": current_user.user_id,
                "email": current_user.email,
                "nickname": current_user.nickname
            }
        },
        message="Token有效"
    )
