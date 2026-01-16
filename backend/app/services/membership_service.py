"""会员服务"""

import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, tuple_
from sqlalchemy.orm import Session

from app.data.initial_packages import (
    get_all_packages,
    get_new_user_bonus,
    get_service_prices,
    get_service_price_variants,
)
from app.models.credit import CreditSource, CreditTransaction
from app.models.membership_package import (
    MembershipPackage,
    NewUserBonus,
    ServicePrice,
    ServicePriceVariant,
    UserMembership,
)
from app.models.user import User
from app.services.credit_math import multiply, to_decimal, to_float
from app.services.service_pricing import resolve_pricing_target


class MembershipService:
    """会员服务"""

    def _serialize_service_price(self, service: ServicePrice) -> Dict[str, Any]:
        """序列化服务价格对象，便于 API 返回"""
        return {
            "id": service.id,
            "service_id": service.service_id,
            "service_name": service.service_name,
            "service_key": service.service_key,
            "description": service.description,
            "price_credits": to_float(service.price_credits),
            "active": service.active,
            "created_at": service.created_at.isoformat()
            if service.created_at
            else None,
            "updated_at": service.updated_at.isoformat()
            if service.updated_at
            else None,
        }

    def _serialize_service_variant(
        self,
        variant: ServicePriceVariant,
        *,
        parent_service: ServicePrice,
        effective_price: Decimal,
    ) -> Dict[str, Any]:
        """序列化服务子模式价格对象"""
        return {
            "id": variant.id,
            "service_id": f"{variant.parent_service_key}_{variant.variant_key}",
            "service_name": (
                f"{parent_service.service_name}-{variant.variant_name}"
                if variant.variant_name
                else parent_service.service_name
            ),
            "service_key": f"{variant.parent_service_key}_{variant.variant_key}",
            "parent_service_key": variant.parent_service_key,
            "variant_key": variant.variant_key,
            "variant_name": variant.variant_name,
            "description": variant.description,
            "price_credits": to_float(effective_price),
            "variant_price_credits": to_float(variant.price_credits)
            if variant.price_credits is not None
            else None,
            "inherits_price": variant.price_credits is None,
            "active": variant.active,
            "created_at": variant.created_at.isoformat()
            if variant.created_at
            else None,
            "updated_at": variant.updated_at.isoformat()
            if variant.updated_at
            else None,
        }

    def _ensure_service_prices_seeded(
        self,
        db: Session,
        target_service_key: Optional[str] = None,
    ) -> None:
        """
        确保默认的服务价格已经写入数据库。
        线上数据库初始化后新增的服务（如平面转3D）不会自动插入，需要在读取前兜底一次。
        """
        base_configs = get_service_prices()
        variant_configs = get_service_price_variants()
        if target_service_key:
            target_service_key = resolve_pricing_target(target_service_key).service_key
            base_configs = [
                cfg for cfg in base_configs if cfg["service_key"] == target_service_key
            ]
            variant_configs = [
                cfg
                for cfg in variant_configs
                if cfg["parent_service_key"] == target_service_key
            ]

        if base_configs:
            keys_to_check = [cfg["service_key"] for cfg in base_configs]
            existing_rows = (
                db.query(ServicePrice.service_key)
                .filter(ServicePrice.service_key.in_(keys_to_check))
                .all()
            )
            existing_keys = {row[0] for row in existing_rows}
            missing_configs = [
                cfg for cfg in base_configs if cfg["service_key"] not in existing_keys
            ]

            for config in missing_configs:
                db.add(ServicePrice(**config))

        if variant_configs:
            keys_to_check = [
                (cfg["parent_service_key"], cfg["variant_key"])
                for cfg in variant_configs
            ]
            existing_rows = (
                db.query(
                    ServicePriceVariant.parent_service_key,
                    ServicePriceVariant.variant_key,
                )
                .filter(
                    tuple_(ServicePriceVariant.parent_service_key, ServicePriceVariant.variant_key).in_(
                        keys_to_check
                    )
                )
                .all()
            )
            existing_keys = {(row[0], row[1]) for row in existing_rows}
            missing_variants = [
                cfg
                for cfg in variant_configs
                if (cfg["parent_service_key"], cfg["variant_key"]) not in existing_keys
            ]

            for config in missing_variants:
                db.add(ServicePriceVariant(**config))

        if base_configs or variant_configs:
            db.commit()

    async def initialize_packages(self, db: Session):
        """初始化套餐数据"""
        # 检查是否已有数据
        existing_packages = db.query(MembershipPackage).count()
        if existing_packages > 0:
            return  # 已有数据，跳过初始化

        # 创建会员套餐
        for package_data in get_all_packages():
            package = MembershipPackage(**package_data)
            db.add(package)

        # 创建服务价格
        for service_data in get_service_prices():
            service = ServicePrice(**service_data)
            db.add(service)

        # 创建服务子模式价格
        for variant_data in get_service_price_variants():
            variant = ServicePriceVariant(**variant_data)
            db.add(variant)

        # 创建新用户福利
        bonus_data = get_new_user_bonus()
        bonus = NewUserBonus(**bonus_data)
        db.add(bonus)

        db.commit()

    async def get_all_packages(
        self, db: Session, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取所有套餐"""
        query = db.query(MembershipPackage).filter(MembershipPackage.active == True)

        if category:
            query = query.filter(MembershipPackage.category == category)

        packages = query.order_by(MembershipPackage.sort_order).all()

        result = []
        for package in packages:
            result.append(
                {
                    "id": package.id,
                    "package_id": package.package_id,
                    "name": package.name,
                    "category": package.category,
                    "description": package.description,
                    "price_yuan": package.price_yuan,
                    "bonus_credits": package.bonus_credits,
                    "total_credits": package.total_credits,
                    "refund_policy": package.refund_policy,
                    "refund_deduction_rate": package.refund_deduction_rate,
                    "privileges": package.privileges or [],
                    "popular": package.popular,
                    "recommended": package.recommended,
                    "sort_order": package.sort_order,
                    "credits_per_yuan": package.credits_per_yuan,
                    "is_refundable": package.is_refundable,
                    "refund_amount_yuan": package.refund_amount_yuan,
                }
            )

        return result

    async def get_service_prices(
        self,
        db: Session,
        include_inactive: bool = False,
        include_variants: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取所有服务价格（默认包含子模式）"""
        self._ensure_service_prices_seeded(db)

        query = db.query(ServicePrice)
        if not include_inactive:
            query = query.filter(ServicePrice.active == True)

        services = query.order_by(ServicePrice.service_key).all()
        service_map = {service.service_key: service for service in services}
        result = [self._serialize_service_price(service) for service in services]

        if include_variants and service_map:
            variant_query = db.query(ServicePriceVariant)
            if not include_inactive:
                variant_query = variant_query.filter(ServicePriceVariant.active == True)

            variants = variant_query.order_by(
                ServicePriceVariant.parent_service_key, ServicePriceVariant.variant_key
            ).all()

            for variant in variants:
                parent_service = service_map.get(variant.parent_service_key)
                if not parent_service:
                    continue
                effective_price = (
                    to_decimal(variant.price_credits)
                    if variant.price_credits is not None
                    else to_decimal(parent_service.price_credits)
                )
                result.append(
                    self._serialize_service_variant(
                        variant,
                        parent_service=parent_service,
                        effective_price=effective_price,
                    )
                )

        result.sort(key=lambda item: item["service_key"])
        return result

    async def get_service_price_groups(
        self, db: Session, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """获取服务价格与子模式分组数据"""
        self._ensure_service_prices_seeded(db)

        query = db.query(ServicePrice)
        if not include_inactive:
            query = query.filter(ServicePrice.active == True)
        services = query.order_by(ServicePrice.service_key).all()
        service_map = {service.service_key: service for service in services}

        variant_query = db.query(ServicePriceVariant)
        if not include_inactive:
            variant_query = variant_query.filter(ServicePriceVariant.active == True)
        variants = variant_query.order_by(
            ServicePriceVariant.parent_service_key, ServicePriceVariant.variant_key
        ).all()

        grouped: Dict[str, Dict[str, Any]] = {}
        for service in services:
            grouped[service.service_key] = {
                **self._serialize_service_price(service),
                "variants": [],
            }

        for variant in variants:
            parent_service = service_map.get(variant.parent_service_key)
            if not parent_service:
                continue
            effective_price = (
                to_decimal(variant.price_credits)
                if variant.price_credits is not None
                else to_decimal(parent_service.price_credits)
            )
            grouped[parent_service.service_key]["variants"].append(
                {
                    "id": variant.id,
                    "variant_key": variant.variant_key,
                    "variant_name": variant.variant_name,
                    "description": variant.description,
                    "price_credits": to_float(variant.price_credits)
                    if variant.price_credits is not None
                    else None,
                    "effective_price_credits": to_float(effective_price),
                    "inherits_price": variant.price_credits is None,
                    "active": variant.active,
                    "created_at": variant.created_at.isoformat()
                    if variant.created_at
                    else None,
                    "updated_at": variant.updated_at.isoformat()
                    if variant.updated_at
                    else None,
                }
            )

        return [
            grouped[key] for key in sorted(grouped.keys())
        ]

    async def get_service_price(self, db: Session, service_key: str) -> Optional[float]:
        """获取特定服务价格"""
        base_key = resolve_pricing_target(service_key).service_key
        self._ensure_service_prices_seeded(db, base_key)

        service = (
            db.query(ServicePrice)
            .filter(
                and_(
                    ServicePrice.service_key == base_key, ServicePrice.active == True
                )
            )
            .first()
        )

        return to_decimal(service.price_credits) if service else None

    async def update_service_price(
        self,
        db: Session,
        service_key: str,
        price_credits: Decimal,
        *,
        service_name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """更新服务价格及相关元数据"""
        service = (
            db.query(ServicePrice)
            .filter(ServicePrice.service_key == service_key)
            .first()
        )

        if not service:
            raise ValueError("SERVICE_NOT_FOUND")

        changes: Dict[str, Any] = {}
        updated = False

        if price_credits is not None:
            new_price = to_decimal(price_credits)
            current_price = to_decimal(service.price_credits)
            if new_price != current_price:
                changes["price_credits"] = {
                    "old": to_float(current_price),
                    "new": to_float(new_price),
                }
                service.price_credits = new_price
                updated = True

        if service_name is not None and service.service_name != service_name:
            changes["service_name"] = {"old": service.service_name, "new": service_name}
            service.service_name = service_name
            updated = True

        if description is not None and service.description != description:
            changes["description"] = {"old": service.description, "new": description}
            service.description = description
            updated = True

        if active is not None and service.active != active:
            changes["active"] = {"old": service.active, "new": active}
            service.active = active
            updated = True

        if updated:
            db.commit()
            db.refresh(service)

        return {
            "service": self._serialize_service_price(service),
            "changes": changes,
            "updated": updated,
        }

    async def update_service_variant_price(
        self,
        db: Session,
        parent_service_key: str,
        variant_key: str,
        *,
        price_credits: Optional[Decimal] = None,
        inherit_price: Optional[bool] = None,
        variant_name: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """更新服务子模式价格及元数据"""
        variant = (
            db.query(ServicePriceVariant)
            .filter(
                ServicePriceVariant.parent_service_key == parent_service_key,
                ServicePriceVariant.variant_key == variant_key,
            )
            .first()
        )

        if not variant:
            raise ValueError("VARIANT_NOT_FOUND")

        parent_service = (
            db.query(ServicePrice)
            .filter(ServicePrice.service_key == parent_service_key)
            .first()
        )
        if not parent_service:
            raise ValueError("SERVICE_NOT_FOUND")

        changes: Dict[str, Any] = {}
        updated = False

        if inherit_price is True:
            if variant.price_credits is not None:
                changes["price_credits"] = {
                    "old": to_float(to_decimal(variant.price_credits)),
                    "new": None,
                }
                variant.price_credits = None
                updated = True
        elif price_credits is not None:
            new_price = to_decimal(price_credits)
            current_price = (
                to_decimal(variant.price_credits)
                if variant.price_credits is not None
                else None
            )
            if current_price != new_price:
                changes["price_credits"] = {
                    "old": to_float(current_price) if current_price is not None else None,
                    "new": to_float(new_price),
                }
                variant.price_credits = new_price
                updated = True

        if variant_name is not None and variant.variant_name != variant_name:
            changes["variant_name"] = {
                "old": variant.variant_name,
                "new": variant_name,
            }
            variant.variant_name = variant_name
            updated = True

        if description is not None and variant.description != description:
            changes["description"] = {"old": variant.description, "new": description}
            variant.description = description
            updated = True

        if active is not None and variant.active != active:
            changes["active"] = {"old": variant.active, "new": active}
            variant.active = active
            updated = True

        if updated:
            db.commit()
            db.refresh(variant)

        effective_price = (
            to_decimal(variant.price_credits)
            if variant.price_credits is not None
            else to_decimal(parent_service.price_credits)
        )

        return {
            "variant": {
                "id": variant.id,
                "parent_service_key": parent_service_key,
                "variant_key": variant.variant_key,
                "variant_name": variant.variant_name,
                "description": variant.description,
                "price_credits": to_float(variant.price_credits)
                if variant.price_credits is not None
                else None,
                "effective_price_credits": to_float(effective_price),
                "inherits_price": variant.price_credits is None,
                "active": variant.active,
                "created_at": variant.created_at.isoformat()
                if variant.created_at
                else None,
                "updated_at": variant.updated_at.isoformat()
                if variant.updated_at
                else None,
            },
            "changes": changes,
            "updated": updated,
        }

    async def purchase_package(
        self,
        db: Session,
        user_id: int,
        package_id: str,
        payment_method: str,
        order_id: str,
    ) -> Dict[str, Any]:
        """购买套餐"""

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")

        # 获取套餐
        package = (
            db.query(MembershipPackage)
            .filter(
                and_(
                    MembershipPackage.package_id == package_id,
                    MembershipPackage.active == True,
                )
            )
            .first()
        )

        if not package:
            raise Exception("套餐不存在或已下架")

        # 创建用户会员记录
        user_membership = UserMembership(
            user_id=user_id,
            package_id=package_id,
            purchase_amount_yuan=package.price_yuan,
            total_credits_received=package.total_credits,
            order_id=order_id,
            activated_at=datetime.utcnow(),
        )

        db.add(user_membership)

        # 增加用户积分
        user.add_credits(to_decimal(package.total_credits))

        # 记录积分交易
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="earn",
            amount=to_decimal(package.total_credits),
            balance_after=to_decimal(user.credits or 0),
            source=CreditSource.PURCHASE.value,
            description=f"购买 {package.name}",
            related_order_id=order_id,
            details=json.dumps(
                {
                    "package_id": package.package_id,
                    "package_name": package.name,
                    "price_yuan": package.price_yuan,
                    "bonus_credits": package.bonus_credits,
                    "total_credits": package.total_credits,
                    "payment_method": payment_method,
                },
                ensure_ascii=False,
            ),
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "user_membership_id": user_membership.id,
            "credits_added": to_float(package.total_credits),
            "new_balance": to_float(user.credits),
            "package_info": {
                "name": package.name,
                "price_yuan": package.price_yuan,
                "bonus_credits": package.bonus_credits,
                "total_credits": package.total_credits,
            },
        }

    async def refund_package(
        self, db: Session, user_id: int, user_membership_id: int, reason: str
    ) -> Dict[str, Any]:
        """退款套餐"""

        # 获取用户会员记录
        user_membership = (
            db.query(UserMembership)
            .filter(
                and_(
                    UserMembership.id == user_membership_id,
                    UserMembership.user_id == user_id,
                )
            )
            .first()
        )

        if not user_membership:
            raise Exception("会员记录不存在")

        if user_membership.is_refunded:
            raise Exception("该会员记录已退款")

        # 获取套餐信息
        package = (
            db.query(MembershipPackage)
            .filter(MembershipPackage.package_id == user_membership.package_id)
            .first()
        )

        if not package:
            raise Exception("套餐信息不存在")

        if not package.is_refundable:
            raise Exception("该套餐不可退款")

        # 计算退款金额
        refund_amount_yuan = int(package.refund_amount_yuan)

        # 更新用户会员记录
        user_membership.refunded_at = datetime.utcnow()
        user_membership.refund_amount_yuan = refund_amount_yuan
        user_membership.refund_reason = reason
        user_membership.is_active = False

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()

        # 扣除积分（只扣除实际支付金额对应的积分，赠送积分不扣除）
        credits_to_deduct = to_decimal(
            user_membership.purchase_amount_yuan
        )  # 1元=1积分

        if not user.can_afford(credits_to_deduct):
            raise Exception("用户积分不足，无法完成退款")

        user.deduct_credits(credits_to_deduct)

        # 记录退款交易
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="spend",
            amount=-credits_to_deduct,
            balance_after=to_decimal(user.credits or 0),
            source=CreditSource.REFUND.value,
            description=f"套餐退款: {package.name}",
            related_order_id=user_membership.order_id,
            details=json.dumps(
                {
                    "refund_amount_yuan": refund_amount_yuan,
                    "refund_reason": reason,
                    "original_purchase_amount": user_membership.purchase_amount_yuan,
                    "deduction_rate": package.refund_deduction_rate,
                },
                ensure_ascii=False,
            ),
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "refund_amount_yuan": refund_amount_yuan,
            "credits_deducted": to_float(credits_to_deduct),
            "new_balance": to_float(user.credits),
            "refund_reason": reason,
        }

    async def apply_new_user_bonus(self, db: Session, user_id: int) -> Dict[str, Any]:
        """应用新用户福利"""

        # 检查是否已经领取过福利
        existing_bonus = (
            db.query(CreditTransaction)
            .filter(
                and_(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.source == CreditSource.REGISTRATION.value,
                )
            )
            .first()
        )

        if existing_bonus:
            return {"success": False, "message": "已经领取过新用户福利"}

        # 获取新用户福利配置
        bonus_config = (
            db.query(NewUserBonus).filter(NewUserBonus.active == True).first()
        )

        if not bonus_config:
            return {"success": False, "message": "新用户福利未配置"}

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "用户不存在"}

        # 增加用户积分
        user.add_credits(to_decimal(bonus_config.bonus_credits))

        # 记录积分交易
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="earn",
            amount=to_decimal(bonus_config.bonus_credits),
            balance_after=to_decimal(user.credits or 0),
            source=CreditSource.REGISTRATION.value,
            description="新用户注册福利",
            details=json.dumps(
                {
                    "bonus_type": "new_user",
                    "bonus_credits": bonus_config.bonus_credits,
                },
                ensure_ascii=False,
            ),
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "bonus_credits": bonus_config.bonus_credits,
            "new_balance": to_float(user.credits),
            "message": "新用户福利已发放",
        }

    async def get_user_memberships(
        self, db: Session, user_id: int
    ) -> List[Dict[str, Any]]:
        """获取用户会员记录"""
        memberships = (
            db.query(UserMembership)
            .filter(UserMembership.user_id == user_id)
            .order_by(UserMembership.purchased_at.desc())
            .all()
        )

        result = []
        for membership in memberships:
            package = (
                db.query(MembershipPackage)
                .filter(MembershipPackage.package_id == membership.package_id)
                .first()
            )

            result.append(
                {
                    "id": membership.id,
                    "package_id": membership.package_id,
                    "package_name": package.name if package else "未知套餐",
                    "purchase_amount_yuan": membership.purchase_amount_yuan,
                    "total_credits_received": membership.total_credits_received,
                    "is_active": membership.is_active,
                    "purchased_at": membership.purchased_at,
                    "activated_at": membership.activated_at,
                    "expires_at": membership.expires_at,
                    "is_refunded": membership.is_refunded,
                    "refund_amount_yuan": membership.refund_amount_yuan,
                    "refund_reason": membership.refund_reason,
                    "order_id": membership.order_id,
                }
            )

        return result

    async def calculate_service_cost(
        self,
        db: Session,
        service_key: str,
        quantity: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> Optional[Decimal]:
        """计算服务成本，支持基于选项的变体计价"""
        self._ensure_service_prices_seeded(db, service_key)
        pricing_target = resolve_pricing_target(service_key, options)

        base_price = await self.get_service_price(db, pricing_target.service_key)
        if base_price is None:
            return None

        effective_price = base_price
        if pricing_target.variant_key:
            variant = (
                db.query(ServicePriceVariant)
                .filter(
                    ServicePriceVariant.parent_service_key
                    == pricing_target.service_key,
                    ServicePriceVariant.variant_key == pricing_target.variant_key,
                )
                .first()
            )
            if variant and variant.active:
                if variant.price_credits is not None:
                    effective_price = to_decimal(variant.price_credits)

        return multiply(effective_price, quantity)

    async def can_afford_service(
        self,
        db: Session,
        user_id: int,
        service_key: str,
        quantity: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """检查用户是否能支付服务费用"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员用户有无限积分
        if user.is_admin:
            return True

        cost = await self.calculate_service_cost(db, service_key, quantity, options)
        if cost is None:
            return False

        return to_decimal(user.credits or 0) >= cost

    async def deduct_service_cost(
        self,
        db: Session,
        user_id: int,
        service_key: str,
        task_id: str,
        quantity: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """扣除服务费用"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员用户不需要扣除积分
        if user.is_admin:
            return True

        cost = await self.calculate_service_cost(db, service_key, quantity, options)
        if cost is None:
            return False

        if not user.can_afford(cost):
            return False

        # 扣除积分
        user.deduct_credits(cost)

        # 记录积分交易
        service = (
            db.query(ServicePrice)
            .filter(ServicePrice.service_key == service_key)
            .first()
        )
        service_name = service.service_name if service else service_key

        pricing_target = resolve_pricing_target(service_key, options)
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="spend",
            amount=-cost,
            balance_after=to_decimal(user.credits or 0),
            source="processing",
            description=f"使用 {service_name}",
            related_task_id=task_id,
            details={
                "service_key": service_key,
                "pricing_key": pricing_target.pricing_key,
                "variant_key": pricing_target.variant_key,
                "service_name": service_name,
                "quantity": quantity,
                "unit_price": to_float(cost / quantity),
                "total_cost": to_float(cost),
            },
        )

        db.add(transaction)
        db.commit()

        return True
