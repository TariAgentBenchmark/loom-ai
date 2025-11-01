"""支付服务"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.membership_package import MembershipPackage
from app.models.payment import Order, OrderStatus, PaymentMethod, PackageType
from app.models.user import User


class PaymentService:
    """聚合收银台支付服务"""

    def __init__(self) -> None:
        base_url = settings.payment_gateway_base_url.rstrip("/")
        create_path = settings.payment_gateway_create_path.lstrip("/")
        query_path = settings.payment_gateway_query_path.lstrip("/")

        self.logger = logging.getLogger(__name__)
        self.counter_config = {
            "create_url": f"{base_url}/{create_path}",
            "query_url": f"{base_url}/{query_path}",
            "version": settings.payment_gateway_version,
            "merchant_no": settings.payment_gateway_merchant_no,
            "channel_id": settings.payment_gateway_channel_id,
            "vpos_id": settings.payment_gateway_vpos_id,
            "notify_url": settings.payment_gateway_notify_url
            or f"{settings.base_url.rstrip('/')}/api/v1/payment/aggregate/notify",
            "callback_url": settings.payment_gateway_callback_url
            or settings.base_url.rstrip("/"),
            "sign_key": settings.payment_gateway_sign_key,
            "timeout": settings.payment_gateway_timeout_seconds,
        }

    async def create_order(
        self,
        db: Session,
        user_id: int,
        package_id: str,
        payment_method: Optional[str] = None,
        coupon_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建支付订单"""

        method = payment_method or PaymentMethod.LAKALA_COUNTER.value
        if method != PaymentMethod.LAKALA_COUNTER.value:
            raise Exception("当前仅支持聚合收银台支付")

        if not self.counter_config["merchant_no"]:
            raise Exception("支付通道未配置商户号，请联系管理员")

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")

        # 获取套餐
        package = (
            db.query(MembershipPackage)
            .filter(MembershipPackage.package_id == package_id)
            .first()
        )
        if not package:
            raise Exception("套餐不存在")

        # 计算价格（单位：分）
        original_amount = int(package.price_yuan * 100)
        discount_amount = 0
        final_amount = original_amount - discount_amount

        # 生成订单ID
        order_id = f"order_{uuid.uuid4().hex[:24]}"

        expires_at = datetime.utcnow() + timedelta(hours=2)

        order = Order(
            order_id=order_id,
            user_id=user_id,
            package_id=package.package_id,
            package_name=package.name,
            package_type=PackageType.MEMBERSHIP.value,
            original_amount=original_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            payment_method=method,
            status=OrderStatus.PENDING.value,
            coupon_code=coupon_code,
            coupon_discount=discount_amount,
            credits_amount=package.total_credits,
            expires_at=expires_at,
            extra_metadata={
                "payment_gateway": "lakala_counter",
                "package_name": package.name,
            },
        )

        db.add(order)
        db.flush()

        try:
            gateway_data = self._create_counter_order(order, package)
        except Exception:
            db.rollback()
            raise

        extra_metadata = order.extra_metadata or {}
        extra_metadata.update(
            {
                "payment_gateway": "lakala_counter",
                "pay_order_no": gateway_data.get("pay_order_no"),
                "merchant_no": gateway_data.get("merchant_no"),
                "channel_id": gateway_data.get("channel_id"),
            }
        )

        order.payment_url = gateway_data.get("counter_url")
        order.qr_code_url = None
        order.extra_metadata = extra_metadata

        db.commit()
        db.refresh(order)

        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "package_id": package.package_id,
            "package_name": package.name,
            "original_amount": original_amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "payment_method": method,
            "status": order.status,
            "payment_url": order.payment_url,
            "qr_code_url": order.qr_code_url,
            "expires_at": order.expires_at.isoformat(),
            "created_at": order.created_at.isoformat(),
            "pay_order_no": gateway_data.get("pay_order_no"),
        }

    def _create_counter_order(
        self,
        order: Order,
        package: MembershipPackage,
    ) -> Dict[str, Any]:
        """调用聚合收银台创建订单"""

        req_data: Dict[str, Any] = {
            "out_order_no": order.order_id,
            "merchant_no": self.counter_config["merchant_no"],
            "total_amount": str(order.final_amount),
            "order_efficient_time": order.expires_at.strftime("%Y%m%d%H%M%S"),
            "notify_url": self.counter_config["notify_url"],
            "callback_url": self.counter_config["callback_url"],
            "support_cancel": "0",
            "support_refund": "1",
            "support_repeat_pay": "1",
            "order_info": package.name[:64],
        }

        if self.counter_config.get("channel_id"):
            req_data["channel_id"] = self.counter_config["channel_id"]
        if self.counter_config.get("vpos_id"):
            req_data["vpos_id"] = self.counter_config["vpos_id"]

        payload = self._wrap_request_payload(req_data)
        response_data = self._request_gateway(
            self.counter_config["create_url"], payload
        )

        resp_data = response_data.get("resp_data")
        if not resp_data:
            raise Exception("聚合收银台返回数据异常")

        return resp_data

    def _request_gateway(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """向支付网关发送请求"""

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.counter_config["timeout"],
                headers={"Content-Type": "application/json"},
            )
        except requests.RequestException as exc:
            self.logger.error("调用聚合收银台失败: %s", exc)
            raise Exception("聚合收银台网络请求失败") from exc

        if response.status_code != 200:
            self.logger.error(
                "聚合收银台响应异常: status=%s body=%s",
                response.status_code,
                response.text,
            )
            raise Exception("聚合收银台响应异常")

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            self.logger.error("聚合收银台返回非JSON数据: %s", response.text)
            raise Exception("聚合收银台返回数据解析失败") from exc

        code = data.get("code")
        if code not in ("000000", "SUCCESS"):
            msg = data.get("msg", "未知错误")
            raise Exception(f"聚合收银台下单失败: {msg}")

        return data

    def _wrap_request_payload(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """构造标准请求报文"""

        payload = {
            "req_time": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "version": self.counter_config["version"],
            "req_data": req_data,
        }

        sign_key = self.counter_config.get("sign_key")
        if sign_key:
            payload["sign"] = self._generate_counter_sign(payload, sign_key)

        return payload

    def _generate_counter_sign(self, payload: Dict[str, Any], secret: str) -> str:
        """生成聚合收银台签名"""

        req_data = payload.get("req_data", {})
        sign_str = json.dumps(
            req_data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        raw = f"{sign_str}{secret}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()

    async def handle_counter_notify(
        self,
        db: Session,
        notify_data: Dict[str, Any],
    ) -> bool:
        """处理聚合收银台异步通知"""

        out_order_no = notify_data.get("out_order_no")
        if not out_order_no:
            return False

        order = db.query(Order).filter(Order.order_id == out_order_no).first()
        if not order:
            return False

        extra = order.extra_metadata or {}
        extra["notify_payload"] = notify_data
        if notify_data.get("pay_order_no"):
            extra["pay_order_no"] = notify_data["pay_order_no"]
        order.extra_metadata = extra

        order_status = str(notify_data.get("order_status", ""))
        trade_info = notify_data.get("order_trade_info") or {}

        status_changed = self._apply_gateway_status(order, order_status, trade_info)

        db.commit()
        db.refresh(order)

        if status_changed and order.status == OrderStatus.PAID.value:
            from app.services.membership_service import MembershipService

            membership_service = MembershipService()
            await membership_service.purchase_package(
                db,
                order.user_id,
                order.package_id,
                order.payment_method,
                order.order_id,
            )

        return True

    def _apply_gateway_status(
        self,
        order: Order,
        gateway_status: str,
        trade_info: Dict[str, Any],
    ) -> bool:
        """根据聚合收银台状态同步本地订单"""

        previous_status = order.status

        if gateway_status == "2":
            transaction_id = self._extract_trade_reference(trade_info)
            order.mark_as_paid(transaction_id or trade_info.get("trade_no") or "")
        elif gateway_status in {"3", "4"}:
            order.status = OrderStatus.FAILED.value
        elif gateway_status in {"5", "7"}:
            order.status = OrderStatus.CANCELLED.value
        elif gateway_status == "6":
            order.status = OrderStatus.REFUNDED.value

        if trade_info:
            extra = order.extra_metadata or {}
            extra["last_trade_info"] = trade_info
            order.extra_metadata = extra

        return previous_status != order.status

    def _extract_trade_reference(self, trade_info: Dict[str, Any]) -> Optional[str]:
        """提取交易流水号"""
        for key in ("trade_no", "acc_trade_no", "sub_trade_no", "log_no"):
            value = trade_info.get(key)
            if value:
                return str(value)
        return None

    async def get_order_status(
        self,
        db: Session,
        order_id: str,
    ) -> Dict[str, Any]:
        """获取订单状态"""

        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise Exception("订单不存在")

        if order.status == OrderStatus.PENDING.value:
            try:
                gateway_data = self._query_counter_order(order)
            except Exception as exc:
                self.logger.warning("查询聚合收银台订单失败: %s", exc)
                gateway_data = None

            if gateway_data:
                order_status = str(gateway_data.get("order_status", ""))
                trade_info = {}
                trade_list = gateway_data.get("order_trade_info_list")
                if isinstance(trade_list, list) and trade_list:
                    trade_info = trade_list[0]

                status_changed = self._apply_gateway_status(
                    order,
                    order_status,
                    trade_info,
                )

                extra = order.extra_metadata or {}
                extra["last_query_response"] = gateway_data
                order.extra_metadata = extra

                if status_changed:
                    db.commit()
                    db.refresh(order)
                else:
                    db.commit()

        return {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "final_amount": order.final_amount,
            "package_name": order.package_name,
            "payment_url": order.payment_url,
            "created_at": order.created_at.isoformat(),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "expires_at": order.expires_at.isoformat(),
            "is_expired": order.is_expired,
            "extra_metadata": order.extra_metadata or {},
        }

    def _query_counter_order(self, order: Order) -> Optional[Dict[str, Any]]:
        """查询聚合收银台订单状态"""

        pay_order_no = None
        if order.extra_metadata:
            pay_order_no = order.extra_metadata.get("pay_order_no")

        req_data: Dict[str, Any] = {"merchant_no": self.counter_config["merchant_no"]}

        if pay_order_no:
            req_data["pay_order_no"] = pay_order_no
        else:
            req_data["out_order_no"] = order.order_id

        if self.counter_config.get("channel_id"):
            req_data["channel_id"] = self.counter_config["channel_id"]

        payload = self._wrap_request_payload(req_data)
        response_data = self._request_gateway(
            self.counter_config["query_url"], payload
        )

        return response_data.get("resp_data")

    async def cancel_order(self, db: Session, order_id: str) -> bool:
        """取消订单"""
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise Exception("订单不存在")

        if not order.can_be_cancelled:
            raise Exception("订单无法取消")

        order.mark_as_cancelled()
        db.commit()

        return True
