#!/usr/bin/env python3
"""
Update membership_packages to new pricing set (sync with frontend).
- Upsert new package IDs (discount_28/discount_66, membership_168/688/1888/5888)
- Deactivate old packages not in the new list
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.membership_package import MembershipPackage, PackageCategory, RefundPolicy

NEW_PACKAGES = [
    {
        "package_id": "membership_168",
        "name": "优惠 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 168,
        "bonus_credits": 30,
        "total_credits": 198,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.33一张图",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "畅享全站功能",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "popular": False,
        "recommended": False,
        "sort_order": 1,
    },
    {
        "package_id": "membership_688",
        "name": "专业 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 688,
        "bonus_credits": 240,
        "total_credits": 928,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.29一张图",
            "畅享全站功能",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "popular": False,
        "recommended": False,
        "sort_order": 2,
    },
    {
        "package_id": "membership_1888",
        "name": "公司 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 1888,
        "bonus_credits": 1088,
        "total_credits": 2976,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.23一张图",
            "畅享全站功能",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "popular": True,
        "recommended": True,
        "sort_order": 3,
    },
    {
        "package_id": "membership_5888",
        "name": "商业 套餐",
        "category": PackageCategory.MEMBERSHIP.value,
        "description": "积分灵活使用",
        "price_yuan": 5888,
        "bonus_credits": 6000,
        "total_credits": 11888,
        "refund_policy": RefundPolicy.REFUNDABLE.value,
        "refund_deduction_rate": 0.2,
        "privileges": [
            "提取约0.18一张图",
            "畅享全站功能",
            "积分永不过期",
            "支持多台电脑登录同一账号",
            "提供开具增值税发票",
            "会员套餐可联系客服退款（赠送不退）",
        ],
        "popular": False,
        "recommended": False,
        "sort_order": 4,
    },
    {
        "package_id": "discount_28",
        "name": "28元试用套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "积分灵活使用",
        "price_yuan": 28,
        "bonus_credits": 2,
        "total_credits": 30,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": ["积分永不过期", "优惠套餐不可退款"],
        "popular": False,
        "recommended": False,
        "sort_order": 5,
    },
    {
        "package_id": "discount_66",
        "name": "66元试用套餐",
        "category": PackageCategory.DISCOUNT.value,
        "description": "积分灵活使用",
        "price_yuan": 66,
        "bonus_credits": 6,
        "total_credits": 72,
        "refund_policy": RefundPolicy.NON_REFUNDABLE.value,
        "refund_deduction_rate": 0.0,
        "privileges": ["提取约0.38一张图", "积分永不过期", "优惠套餐不可退款"],
        "popular": False,
        "recommended": False,
        "sort_order": 6,
    },
]


def get_engine():
    if settings.database_url.startswith("sqlite"):
        return create_engine(settings.database_url, connect_args={"check_same_thread": False, "timeout": 20})
    return create_engine(settings.database_url, pool_pre_ping=True)


def upsert_packages():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        ids = [p["package_id"] for p in NEW_PACKAGES]
        for data in NEW_PACKAGES:
            existing = (
                session.query(MembershipPackage)
                .filter(MembershipPackage.package_id == data["package_id"])
                .first()
            )
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                existing.active = True
            else:
                session.add(MembershipPackage(**data, active=True))

        # deactivate other packages
        session.query(MembershipPackage).filter(~MembershipPackage.package_id.in_(ids)).update(
            {"active": False}, synchronize_session=False
        )
        session.commit()
        print(f"✅ Upserted {len(NEW_PACKAGES)} packages, deactivated others")
    except Exception as exc:  # pragma: no cover
        session.rollback()
        print(f"❌ Update failed: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    upsert_packages()
