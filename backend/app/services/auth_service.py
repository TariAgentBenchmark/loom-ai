import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings
from app.models.user import User, MembershipType, UserStatus

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != token_type:
                return None
            
            # 检查过期时间
            exp = payload.get("exp")
            if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return None
            
            return payload
            
        except JWTError:
            return None

    async def register_user(
        self,
        db: Session,
        email: str,
        password: str,
        nickname: Optional[str] = None,
        phone: Optional[str] = None
    ) -> User:
        """注册新用户"""
        
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise Exception("邮箱已存在")
        
        # 创建新用户
        user = User(
            user_id=f"user_{uuid.uuid4().hex[:12]}",
            email=email,
            hashed_password=self.get_password_hash(password),
            nickname=nickname or email.split("@")[0],
            phone=phone,
            credits=200,  # 新用户赠送200算力
            membership_type=MembershipType.FREE,
            status=UserStatus.ACTIVE
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 记录注册赠送算力
        from app.services.credit_service import CreditService
        credit_service = CreditService()
        await credit_service.record_transaction(
            db=db,
            user_id=user.id,
            amount=200,
            source="registration",
            description="新用户注册赠送"
        )
        
        return user

    async def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """认证用户"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if user.status != UserStatus.ACTIVE:
            raise Exception("账户已被暂停")
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user

    async def authenticate_admin(self, db: Session, email: str, password: str) -> Optional[User]:
        """认证管理员用户"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_admin:
            raise Exception("非管理员账户")
        
        if user.status != UserStatus.ACTIVE:
            raise Exception("管理员账户已被暂停")
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        return user

    async def get_user_by_token(self, db: Session, token: str) -> Optional[User]:
        """通过令牌获取用户"""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.user_id == user_id).first()
        return user

    def generate_reset_token(self) -> str:
        """生成密码重置令牌"""
        return secrets.token_urlsafe(32)

    async def request_password_reset(self, db: Session, email: str) -> Optional[str]:
        """请求密码重置"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        # 生成重置令牌
        reset_token = self.generate_reset_token()
        reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1小时有效
        
        user.reset_token = reset_token
        user.reset_token_expires = reset_expires
        db.commit()
        
        return reset_token

    async def reset_password(
        self,
        db: Session,
        reset_token: str,
        new_password: str
    ) -> bool:
        """重置密码"""
        user = db.query(User).filter(
            User.reset_token == reset_token,
            User.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            return False
        
        # 更新密码
        user.hashed_password = self.get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        
        return True

    async def change_password(
        self,
        db: Session,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = self.get_password_hash(new_password)
        db.commit()
        
        return True

    def create_login_tokens(self, user: User) -> Dict[str, Any]:
        """创建登录令牌"""
        access_token = self.create_access_token(
            data={"sub": user.user_id, "email": user.email, "is_admin": user.is_admin}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.user_id, "email": user.email, "is_admin": user.is_admin}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "is_admin": user.is_admin
        }

    def create_admin_login_tokens(self, user: User) -> Dict[str, Any]:
        """创建管理员登录令牌"""
        if not user.is_admin:
            raise Exception("非管理员账户无法创建管理员令牌")
            
        access_token = self.create_access_token(
            data={"sub": user.user_id, "email": user.email, "is_admin": True, "admin_session": True}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.user_id, "email": user.email, "is_admin": True, "admin_session": True}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "is_admin": True,
            "admin_session": True
        }
