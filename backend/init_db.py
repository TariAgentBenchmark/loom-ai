#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, SessionLocal
from app.models.user import User, MembershipType, UserStatus
from app.models.payment import Package
from app.services.auth_service import AuthService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_packages():
    """创建示例套餐数据"""
    db = SessionLocal()
    
    try:
        # 检查是否已有套餐数据
        existing = db.query(Package).first()
        if existing:
            logger.info("套餐数据已存在，跳过创建")
            return
        
        # 创建示例套餐
        packages = [
            Package(
                package_id="monthly_trial",
                name="试用体验",
                type="membership",
                category="monthly",
                price=0,
                credits=200,
                duration=7,
                features=["赠送200算力积分", "7天内有效", "基础功能"],
                description="免费试用",
                active=True,
                popular=False
            ),
            Package(
                package_id="monthly_basic",
                name="基础版",
                type="membership", 
                category="monthly",
                price=6900,
                original_price=8900,
                credits=7500,
                duration=30,
                features=["每月7500算力积分", "所有基础功能", "优先处理"],
                description="性价比之选",
                active=True,
                popular=True,
                discount_label="限时优惠"
            ),
            Package(
                package_id="credits_basic",
                name="基础算力包",
                type="credits",
                category="credits",
                price=1900,
                credits=1000,
                features=["1000算力积分", "永久有效"],
                description="适合偶尔使用",
                active=True,
                popular=False
            )
        ]
        
        for package in packages:
            db.add(package)
        
        db.commit()
        logger.info("✅ 套餐数据创建成功")
        
    except Exception as e:
        logger.error(f"❌ 创建套餐数据失败: {e}")
        db.rollback()
    finally:
        db.close()


def create_admin_user():
    """创建管理员用户"""
    db = SessionLocal()
    auth_service = AuthService()
    
    try:
        # 检查是否已有管理员
        admin = db.query(User).filter(User.email == "admin@loom-ai.com").first()
        if admin:
            logger.info("管理员用户已存在，跳过创建")
            return
        
        # 创建管理员用户
        admin_user = User(
            user_id="admin_loom_ai",
            email="admin@loom-ai.com",
            hashed_password=auth_service.get_password_hash("admin123456"),
            nickname="管理员",
            credits=999999,
            membership_type=MembershipType.ENTERPRISE,
            status=UserStatus.ACTIVE,
            is_email_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        
        logger.info("✅ 管理员用户创建成功")
        logger.info("📧 邮箱: admin@loom-ai.com")
        logger.info("🔑 密码: admin123456")
        
    except Exception as e:
        logger.error(f"❌ 创建管理员用户失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """主函数"""
    print("🗄️  初始化 LoomAI 数据库...")
    
    try:
        # 初始化数据库表
        init_db()
        logger.info("✅ 数据库表创建成功")
        
        # 创建示例数据
        create_sample_packages()
        create_admin_user()
        
        print("\n🎉 数据库初始化完成!")
        print("📖 现在可以启动服务器了: python run_server.py")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
