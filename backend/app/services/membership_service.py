"""会员服务"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user import User
from app.models.membership_package import MembershipPackage, ServicePrice, UserMembership, NewUserBonus
from app.models.credit import CreditTransaction, CreditSource
from app.data.initial_packages import get_all_packages, get_service_prices, get_new_user_bonus


class MembershipService:
    """会员服务"""

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

        # 创建新用户福利
        bonus_data = get_new_user_bonus()
        bonus = NewUserBonus(**bonus_data)
        db.add(bonus)

        db.commit()

    async def get_all_packages(self, db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有套餐"""
        query = db.query(MembershipPackage).filter(MembershipPackage.active == True)

        if category:
            query = query.filter(MembershipPackage.category == category)

        packages = query.order_by(MembershipPackage.sort_order).all()

        result = []
        for package in packages:
            result.append({
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
                "refund_amount_yuan": package.refund_amount_yuan
            })

        return result

    async def get_service_prices(self, db: Session) -> List[Dict[str, Any]]:
        """获取所有服务价格"""
        services = db.query(ServicePrice).filter(ServicePrice.active == True).all()

        result = []
        for service in services:
            result.append({
                "id": service.id,
                "service_id": service.service_id,
                "service_name": service.service_name,
                "service_key": service.service_key,
                "description": service.description,
                "price_credits": service.price_credits,
                "active": service.active
            })

        return result

    async def get_service_price(self, db: Session, service_key: str) -> Optional[float]:
        """获取特定服务价格"""
        service = db.query(ServicePrice).filter(
            and_(
                ServicePrice.service_key == service_key,
                ServicePrice.active == True
            )
        ).first()

        return service.price_credits if service else None

    async def purchase_package(
        self,
        db: Session,
        user_id: int,
        package_id: str,
        payment_method: str,
        order_id: str
    ) -> Dict[str, Any]:
        """购买套餐"""

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")

        # 获取套餐
        package = db.query(MembershipPackage).filter(
            and_(
                MembershipPackage.package_id == package_id,
                MembershipPackage.active == True
            )
        ).first()

        if not package:
            raise Exception("套餐不存在或已下架")

        # 创建用户会员记录
        user_membership = UserMembership(
            user_id=user_id,
            package_id=package_id,
            purchase_amount_yuan=package.price_yuan,
            total_credits_received=package.total_credits,
            order_id=order_id,
            activated_at=datetime.utcnow()
        )

        db.add(user_membership)

        # 增加用户积分
        user.add_credits(package.total_credits)

        # 记录积分交易
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="earn",
            amount=package.total_credits,
            balance_after=user.credits,
            source=CreditSource.PURCHASE.value,
            description=f"购买 {package.name}",
            related_order_id=order_id,
            details={
                "package_id": package.package_id,
                "package_name": package.name,
                "price_yuan": package.price_yuan,
                "bonus_credits": package.bonus_credits,
                "total_credits": package.total_credits,
                "payment_method": payment_method
            }
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "user_membership_id": user_membership.id,
            "credits_added": package.total_credits,
            "new_balance": user.credits,
            "package_info": {
                "name": package.name,
                "price_yuan": package.price_yuan,
                "bonus_credits": package.bonus_credits,
                "total_credits": package.total_credits
            }
        }

    async def refund_package(
        self,
        db: Session,
        user_id: int,
        user_membership_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """退款套餐"""

        # 获取用户会员记录
        user_membership = db.query(UserMembership).filter(
            and_(
                UserMembership.id == user_membership_id,
                UserMembership.user_id == user_id
            )
        ).first()

        if not user_membership:
            raise Exception("会员记录不存在")

        if user_membership.is_refunded:
            raise Exception("该会员记录已退款")

        # 获取套餐信息
        package = db.query(MembershipPackage).filter(
            MembershipPackage.package_id == user_membership.package_id
        ).first()

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
        credits_to_deduct = user_membership.purchase_amount_yuan  # 1元=1积分

        if user.credits < credits_to_deduct:
            raise Exception("用户积分不足，无法完成退款")

        user.credits -= credits_to_deduct

        # 记录退款交易
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="spend",
            amount=-credits_to_deduct,
            balance_after=user.credits,
            source=CreditSource.REFUND.value,
            description=f"套餐退款: {package.name}",
            related_order_id=user_membership.order_id,
            details={
                "refund_amount_yuan": refund_amount_yuan,
                "refund_reason": reason,
                "original_purchase_amount": user_membership.purchase_amount_yuan,
                "deduction_rate": package.refund_deduction_rate
            }
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "refund_amount_yuan": refund_amount_yuan,
            "credits_deducted": credits_to_deduct,
            "new_balance": user.credits,
            "refund_reason": reason
        }

    async def apply_new_user_bonus(self, db: Session, user_id: int) -> Dict[str, Any]:
        """应用新用户福利"""

        # 检查是否已经领取过福利
        existing_bonus = db.query(CreditTransaction).filter(
            and_(
                CreditTransaction.user_id == user_id,
                CreditTransaction.source == CreditSource.REGISTRATION.value
            )
        ).first()

        if existing_bonus:
            return {
                "success": False,
                "message": "已经领取过新用户福利"
            }

        # 获取新用户福利配置
        bonus_config = db.query(NewUserBonus).filter(NewUserBonus.active == True).first()

        if not bonus_config:
            return {
                "success": False,
                "message": "新用户福利未配置"
            }

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "success": False,
                "message": "用户不存在"
            }

        # 增加用户积分
        user.add_credits(bonus_config.bonus_credits)

        # 记录积分交易
        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="earn",
            amount=bonus_config.bonus_credits,
            balance_after=user.credits,
            source=CreditSource.REGISTRATION.value,
            description="新用户注册福利",
            details={
                "bonus_type": "new_user",
                "bonus_credits": bonus_config.bonus_credits
            }
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "bonus_credits": bonus_config.bonus_credits,
            "new_balance": user.credits,
            "message": "新用户福利已发放"
        }

    async def get_user_memberships(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """获取用户会员记录"""
        memberships = db.query(UserMembership).filter(
            UserMembership.user_id == user_id
        ).order_by(UserMembership.purchased_at.desc()).all()

        result = []
        for membership in memberships:
            package = db.query(MembershipPackage).filter(
                MembershipPackage.package_id == membership.package_id
            ).first()

            result.append({
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
                "order_id": membership.order_id
            })

        return result

    async def calculate_service_cost(self, db: Session, service_key: str, quantity: int = 1) -> Optional[float]:
        """计算服务成本"""
        price = await self.get_service_price(db, service_key)
        if price is None:
            return None

        return price * quantity

    async def can_afford_service(self, db: Session, user_id: int, service_key: str, quantity: int = 1) -> bool:
        """检查用户是否能支付服务费用"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员用户有无限算力
        if user.is_admin:
            return True

        cost = await self.calculate_service_cost(db, service_key, quantity)
        if cost is None:
            return False

        return user.credits >= cost

    async def deduct_service_cost(
        self,
        db: Session,
        user_id: int,
        service_key: str,
        task_id: str,
        quantity: int = 1
    ) -> bool:
        """扣除服务费用"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # 管理员用户不需要扣除算力
        if user.is_admin:
            return True

        cost = await self.calculate_service_cost(db, service_key, quantity)
        if cost is None:
            return False

        if not user.can_afford(int(cost)):
            return False

        # 扣除积分
        user.deduct_credits(int(cost))

        # 记录积分交易
        service = db.query(ServicePrice).filter(ServicePrice.service_key == service_key).first()
        service_name = service.service_name if service else service_key

        transaction = CreditTransaction(
            transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type="spend",
            amount=-int(cost),
            balance_after=user.credits,
            source="processing",
            description=f"使用 {service_name}",
            related_task_id=task_id,
            details={
                "service_key": service_key,
                "service_name": service_name,
                "quantity": quantity,
                "unit_price": cost / quantity,
                "total_cost": cost
            }
        )

        db.add(transaction)
        db.commit()

        return True