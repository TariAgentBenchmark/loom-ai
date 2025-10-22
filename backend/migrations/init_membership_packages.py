"""初始化会员套餐数据迁移脚本"""

import sys
import os
from sqlalchemy.orm import Session

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal
from app.models.membership_package import MembershipPackage, ServicePrice, NewUserBonus
from app.data.initial_packages import MEMBERSHIP_PACKAGES, DISCOUNT_PACKAGES, SERVICE_PRICES, NEW_USER_BONUS


def init_membership_packages():
    """初始化会员套餐数据"""
    db = SessionLocal()

    try:
        print("开始初始化会员套餐数据...")

        # 检查是否已有数据
        existing_packages = db.query(MembershipPackage).count()
        if existing_packages > 0:
            print(f"已有 {existing_packages} 个套餐，跳过初始化")
            return

        # 创建会员套餐
        for package_data in MEMBERSHIP_PACKAGES:
            package = MembershipPackage(**package_data)
            db.add(package)
            print(f"创建会员套餐: {package.name}")

        # 创建优惠套餐
        for package_data in DISCOUNT_PACKAGES:
            package = MembershipPackage(**package_data)
            db.add(package)
            print(f"创建优惠套餐: {package.name}")

        # 创建服务价格
        for service_data in SERVICE_PRICES:
            service = ServicePrice(**service_data)
            db.add(service)
            print(f"创建服务价格: {service.service_name} - {service.price_credits}积分")

        # 创建新用户福利
        bonus = NewUserBonus(**NEW_USER_BONUS)
        db.add(bonus)
        print(f"创建新用户福利: 赠送{bonus.bonus_credits}积分")

        db.commit()
        print("会员套餐数据初始化完成!")

    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


def show_package_summary():
    """显示套餐摘要"""
    db = SessionLocal()

    try:
        print("\n=== 会员套餐数据摘要 ===")

        # 会员套餐
        membership_packages = db.query(MembershipPackage).filter(
            MembershipPackage.category == 'membership'
        ).all()

        print(f"\n👑 会员套餐 ({len(membership_packages)}个):")
        for pkg in membership_packages:
            print(f"  - {pkg.name}: ¥{pkg.price_yuan} → {pkg.total_credits}积分 (每元{pkg.credits_per_yuan:.2f}积分)")

        # 优惠套餐
        discount_packages = db.query(MembershipPackage).filter(
            MembershipPackage.category == 'discount'
        ).all()

        print(f"\n💰 优惠套餐 ({len(discount_packages)}个):")
        for pkg in discount_packages:
            print(f"  - {pkg.name}: ¥{pkg.price_yuan} → {pkg.total_credits}积分 (每元{pkg.credits_per_yuan:.2f}积分)")

        # 服务价格
        services = db.query(ServicePrice).all()
        print(f"\n🛠️ 服务项目 ({len(services)}个):")
        for service in services:
            print(f"  - {service.service_name}: {service.price_credits}积分")

        # 新用户福利
        bonus = db.query(NewUserBonus).first()
        if bonus:
            print(f"\n👤 新用户福利: 赠送{bonus.bonus_credits}积分")

    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_membership_packages()
    show_package_summary()