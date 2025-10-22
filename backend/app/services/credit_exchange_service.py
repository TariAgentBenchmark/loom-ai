"""积分兑换服务"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.membership_package import MembershipPackage, ServicePrice


class CreditExchangeService:
    """积分兑换服务"""

    # 基本兑换率：1元 = 1积分
    EXCHANGE_RATE = 1.0

    async def yuan_to_credits(self, yuan_amount: float) -> int:
        """人民币转积分"""
        return int(yuan_amount * self.EXCHANGE_RATE)

    async def credits_to_yuan(self, credits_amount: int) -> float:
        """积分转人民币"""
        return credits_amount / self.EXCHANGE_RATE

    async def calculate_package_value(self, db: Session, package_id: str) -> Dict[str, Any]:
        """计算套餐价值"""
        package = db.query(MembershipPackage).filter(
            and_(
                MembershipPackage.package_id == package_id,
                MembershipPackage.active == True
            )
        ).first()

        if not package:
            return {
                "success": False,
                "message": "套餐不存在"
            }

        # 计算实际价值
        actual_value_yuan = package.total_credits / self.EXCHANGE_RATE
        discount_rate = (actual_value_yuan - package.price_yuan) / actual_value_yuan * 100

        return {
            "success": True,
            "package_id": package.package_id,
            "package_name": package.name,
            "price_yuan": package.price_yuan,
            "total_credits": package.total_credits,
            "actual_value_yuan": round(actual_value_yuan, 2),
            "discount_rate": round(discount_rate, 1),
            "savings_yuan": round(actual_value_yuan - package.price_yuan, 2),
            "credits_per_yuan": round(package.credits_per_yuan, 2),
            "is_refundable": package.is_refundable
        }

    async def compare_packages(self, db: Session) -> List[Dict[str, Any]]:
        """比较所有套餐的价值"""
        packages = db.query(MembershipPackage).filter(
            MembershipPackage.active == True
        ).order_by(MembershipPackage.price_yuan).all()

        comparison = []
        for package in packages:
            value_analysis = await self.calculate_package_value(db, package.package_id)
            if value_analysis["success"]:
                comparison.append(value_analysis)

        # 按每元获得的积分排序
        comparison.sort(key=lambda x: x["credits_per_yuan"], reverse=True)

        return comparison

    async def get_best_value_package(self, db: Session, budget_yuan: float = None) -> Dict[str, Any]:
        """获取最佳性价比套餐"""
        packages = await self.compare_packages(db)

        if not packages:
            return {
                "success": False,
                "message": "没有可用的套餐"
            }

        if budget_yuan:
            # 在预算范围内选择最佳套餐
            affordable_packages = [
                p for p in packages
                if p["price_yuan"] <= budget_yuan
            ]

            if affordable_packages:
                # 在预算范围内选择每元获得积分最多的套餐
                best_package = max(affordable_packages, key=lambda x: x["credits_per_yuan"])
                return {
                    "success": True,
                    "type": "within_budget",
                    "package": best_package,
                    "budget_yuan": budget_yuan,
                    "remaining_budget": budget_yuan - best_package["price_yuan"]
                }
            else:
                # 预算不足，推荐最便宜的套餐
                cheapest_package = min(packages, key=lambda x: x["price_yuan"])
                return {
                    "success": True,
                    "type": "budget_insufficient",
                    "package": cheapest_package,
                    "budget_yuan": budget_yuan,
                    "additional_needed": cheapest_package["price_yuan"] - budget_yuan
                }
        else:
            # 没有预算限制，选择性价比最高的套餐
            best_package = packages[0]  # 已经按性价比排序
            return {
                "success": True,
                "type": "best_value",
                "package": best_package
            }

    async def calculate_service_cost_in_yuan(self, db: Session, service_key: str, quantity: int = 1) -> float:
        """计算服务的人民币成本"""
        service = db.query(ServicePrice).filter(
            and_(
                ServicePrice.service_key == service_key,
                ServicePrice.active == True
            )
        ).first()

        if not service:
            return 0.0

        total_credits = service.price_credits * quantity
        return await self.credits_to_yuan(total_credits)

    async def estimate_usage_cost(
        self,
        db: Session,
        service_usage: Dict[str, int]
    ) -> Dict[str, Any]:
        """估算使用成本"""
        total_credits = 0
        total_yuan = 0.0
        service_details = []

        for service_key, quantity in service_usage.items():
            service = db.query(ServicePrice).filter(
                and_(
                    ServicePrice.service_key == service_key,
                    ServicePrice.active == True
                )
            ).first()

            if service:
                service_credits = service.price_credits * quantity
                service_yuan = await self.credits_to_yuan(service_credits)

                total_credits += service_credits
                total_yuan += service_yuan

                service_details.append({
                    "service_name": service.service_name,
                    "service_key": service.service_key,
                    "quantity": quantity,
                    "unit_price_credits": service.price_credits,
                    "total_credits": service_credits,
                    "total_yuan": round(service_yuan, 2)
                })

        # 推荐合适的套餐
        recommended_package = await self.get_best_value_package(db, total_yuan)

        return {
            "total_credits": total_credits,
            "total_yuan": round(total_yuan, 2),
            "service_details": service_details,
            "recommended_package": recommended_package if recommended_package["success"] else None
        }

    async def get_exchange_rate_info(self) -> Dict[str, Any]:
        """获取兑换率信息"""
        return {
            "exchange_rate": self.EXCHANGE_RATE,
            "description": "1元人民币 = 1积分",
            "last_updated": "2025-10-22",
            "is_fixed": True
        }

    async def calculate_refund_amount(
        self,
        package: MembershipPackage,
        usage_credits: int = 0
    ) -> Dict[str, Any]:
        """计算退款金额"""
        if not package.is_refundable:
            return {
                "success": False,
                "message": "该套餐不可退款"
            }

        # 计算可退金额
        refundable_amount_yuan = package.refund_amount_yuan

        # 如果使用了积分，需要扣除已使用的积分对应的金额
        if usage_credits > 0:
            used_amount_yuan = await self.credits_to_yuan(usage_credits)
            refundable_amount_yuan = max(0, refundable_amount_yuan - used_amount_yuan)

        return {
            "success": True,
            "original_purchase_amount": package.price_yuan,
            "refund_deduction_rate": package.refund_deduction_rate,
            "base_refund_amount": package.refund_amount_yuan,
            "usage_credits": usage_credits,
            "usage_amount_yuan": await self.credits_to_yuan(usage_credits),
            "final_refund_amount": round(refundable_amount_yuan, 2),
            "currency": "CNY"
        }