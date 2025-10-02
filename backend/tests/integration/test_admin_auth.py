"""
管理员认证测试脚本
用于验证管理员认证和授权功能是否正常工作
"""

import asyncio
import json
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import get_db, init_db
from app.models.user import User, UserStatus
from app.services.auth_service import AuthService


async def test_admin_authentication():
    """测试管理员认证功能"""
    print("开始测试管理员认证功能...")
    
    # 初始化数据库
    init_db()
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 创建认证服务实例
        auth_service = AuthService()
        
        # 1. 检查是否存在管理员用户，如果不存在则创建一个
        admin_email = "admin@test.com"
        admin_password = "admin123456"
        
        admin_user = db.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            print(f"创建测试管理员用户: {admin_email}")
            admin_user = User(
                user_id=f"admin_{auth_service.get_password_hash(admin_email)[:12]}",
                email=admin_email,
                hashed_password=auth_service.get_password_hash(admin_password),
                nickname="Admin",
                is_admin=True,
                status=UserStatus.ACTIVE,
                credits=999999  # 管理员拥有大量算力
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("管理员用户创建成功")
        else:
            print(f"管理员用户已存在: {admin_email}")
            # 确保是管理员
            if not admin_user.is_admin:
                admin_user.is_admin = True
                db.commit()
                print("已将用户设置为管理员")
        
        # 2. 测试管理员认证
        print("\n测试管理员认证...")
        authenticated_admin = await auth_service.authenticate_admin(
            db=db,
            email=admin_email,
            password=admin_password
        )
        
        if authenticated_admin:
            print("✓ 管理员认证成功")
            print(f"  用户ID: {authenticated_admin.user_id}")
            print(f"  邮箱: {authenticated_admin.email}")
            print(f"  是否管理员: {authenticated_admin.is_admin}")
        else:
            print("✗ 管理员认证失败")
            return
        
        # 3. 测试创建管理员令牌
        print("\n测试创建管理员令牌...")
        admin_tokens = auth_service.create_admin_login_tokens(authenticated_admin)
        print("✓ 管理员令牌创建成功")
        print(f"  访问令牌: {admin_tokens['access_token'][:50]}...")
        print(f"  刷新令牌: {admin_tokens['refresh_token'][:50]}...")
        print(f"  是否管理员会话: {admin_tokens.get('admin_session', False)}")
        
        # 4. 测试令牌验证
        print("\n测试令牌验证...")
        payload = auth_service.verify_token(admin_tokens['access_token'])
        if payload:
            print("✓ 令牌验证成功")
            print(f"  用户ID: {payload.get('sub')}")
            print(f"  是否管理员: {payload.get('is_admin')}")
            print(f"  管理员会话: {payload.get('admin_session')}")
        else:
            print("✗ 令牌验证失败")
        
        # 5. 测试普通用户认证（非管理员）
        print("\n测试普通用户认证...")
        normal_email = "user@test.com"
        normal_password = "user123456"
        
        normal_user = db.query(User).filter(User.email == normal_email).first()
        if not normal_user:
            print(f"创建测试普通用户: {normal_email}")
            normal_user = User(
                user_id=f"user_{auth_service.get_password_hash(normal_email)[:12]}",
                email=normal_email,
                hashed_password=auth_service.get_password_hash(normal_password),
                nickname="Normal User",
                is_admin=False,
                status=UserStatus.ACTIVE,
                credits=100
            )
            db.add(normal_user)
            db.commit()
            db.refresh(normal_user)
        
        # 尝试使用管理员认证方法认证普通用户
        try:
            await auth_service.authenticate_admin(
                db=db,
                email=normal_email,
                password=normal_password
            )
            print("✗ 非管理员用户通过了管理员认证（应该失败）")
        except Exception as e:
            if "非管理员账户" in str(e):
                print("✓ 非管理员用户正确被拒绝管理员认证")
            else:
                print(f"✗ 意外错误: {str(e)}")
        
        print("\n所有测试完成！管理员认证功能正常工作。")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_admin_authentication())