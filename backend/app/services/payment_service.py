"""支付服务"""

import uuid
import hashlib
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
import requests
from sqlalchemy.orm import Session

from app.models.payment import Order, OrderStatus, PaymentMethod, PackageType
from app.models.membership_package import MembershipPackage
from app.models.user import User
from app.core.config import settings


class PaymentService:
    """支付服务"""

    def __init__(self):
        self.wechat_config = {
            "app_id": settings.WECHAT_APP_ID,
            "mch_id": settings.WECHAT_MCH_ID,
            "api_key": settings.WECHAT_API_KEY,
            "notify_url": f"{settings.BASE_URL}/api/v1/payment/wechat/notify",
            "sandbox": settings.WECHAT_SANDBOX
        }

        self.alipay_config = {
            "app_id": settings.ALIPAY_APP_ID,
            "private_key": settings.ALIPAY_PRIVATE_KEY,
            "alipay_public_key": settings.ALIPAY_PUBLIC_KEY,
            "notify_url": f"{settings.BASE_URL}/api/v1/payment/alipay/notify",
            "return_url": f"{settings.BASE_URL}/payment/success",
            "sandbox": settings.ALIPAY_SANDBOX
        }

    async def create_order(
        self,
        db: Session,
        user_id: int,
        package_id: str,
        payment_method: str,
        coupon_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建支付订单"""

        # 获取用户
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("用户不存在")

        # 获取套餐
        package = db.query(MembershipPackage).filter(
            MembershipPackage.package_id == package_id
        ).first()

        if not package:
            raise Exception("套餐不存在")

        # 计算价格（单位：分）
        original_amount = int(package.price_yuan * 100)
        discount_amount = 0
        final_amount = original_amount - discount_amount

        # 生成订单ID
        order_id = f"order_{uuid.uuid4().hex[:12]}"

        # 创建订单
        order = Order(
            order_id=order_id,
            user_id=user_id,
            package_id=package.package_id,
            package_name=package.name,
            package_type=PackageType.MEMBERSHIP.value,
            original_amount=original_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            payment_method=payment_method,
            status=OrderStatus.PENDING.value,
            coupon_code=coupon_code,
            coupon_discount=discount_amount,
            credits_amount=package.total_credits,
            expires_at=datetime.utcnow() + timedelta(hours=2)
        )

        db.add(order)
        db.commit()

        # 根据支付方式生成支付信息
        payment_info = {}
        if payment_method == PaymentMethod.WECHAT.value:
            payment_info = await self._create_wechat_payment(order)
        elif payment_method == PaymentMethod.ALIPAY.value:
            payment_info = await self._create_alipay_payment(order)
        else:
            raise Exception("不支持的支付方式")

        # 更新订单支付信息
        order.payment_url = payment_info.get("payment_url")
        order.qr_code_url = payment_info.get("qr_code_url")
        db.commit()

        return {
            "order_id": order.order_id,
            "package_id": package.package_id,
            "package_name": package.name,
            "original_amount": original_amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
            "payment_method": payment_method,
            "status": order.status,
            "payment_url": order.payment_url,
            "qr_code_url": order.qr_code_url,
            "expires_at": order.expires_at.isoformat(),
            "created_at": order.created_at.isoformat()
        }

    async def _create_wechat_payment(self, order: Order) -> Dict[str, Any]:
        """创建微信支付"""

        # 微信支付API基础URL
        base_url = "https://api.mch.weixin.qq.com"
        if self.wechat_config["sandbox"]:
            base_url = "https://api.mch.weixin.qq.com/sandboxnew"

        # 构建请求参数
        params = {
            "appid": self.wechat_config["app_id"],
            "mch_id": self.wechat_config["mch_id"],
            "nonce_str": self._generate_nonce_str(),
            "body": f"LoomAI - {order.package_name}",
            "out_trade_no": order.order_id,
            "total_fee": order.final_amount,  # 单位：分
            "spbill_create_ip": "127.0.0.1",  # 实际应该获取用户IP
            "notify_url": self.wechat_config["notify_url"],
            "trade_type": "NATIVE",  # 扫码支付
            "time_expire": order.expires_at.strftime("%Y%m%d%H%M%S")
        }

        # 生成签名
        params["sign"] = self._generate_wechat_sign(params)

        # 发送请求
        xml_data = self._dict_to_xml(params)
        response = requests.post(
            f"{base_url}/pay/unifiedorder",
            data=xml_data,
            headers={'Content-Type': 'application/xml'}
        )

        if response.status_code != 200:
            raise Exception("微信支付请求失败")

        # 解析响应
        result = self._xml_to_dict(response.text)

        if result.get("return_code") != "SUCCESS":
            raise Exception(f"微信支付失败: {result.get('return_msg', '未知错误')}")

        if result.get("result_code") != "SUCCESS":
            raise Exception(f"微信支付业务失败: {result.get('err_code_des', '未知错误')}")

        return {
            "payment_url": result.get("code_url"),
            "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={result.get('code_url')}"
        }

    async def _create_alipay_payment(self, order: Order) -> Dict[str, Any]:
        """创建支付宝支付"""

        # 支付宝网关
        gateway = "https://openapi.alipay.com/gateway.do"
        if self.alipay_config["sandbox"]:
            gateway = "https://openapi.alipaydev.com/gateway.do"

        # 构建请求参数
        biz_content = {
            "out_trade_no": order.order_id,
            "total_amount": order.final_amount / 100.0,  # 转换为元
            "subject": f"LoomAI - {order.package_name}",
            "body": order.package_name,
            "timeout_express": "2h",
            "product_code": "FAST_INSTANT_TRADE_PAY"
        }

        params = {
            "app_id": self.alipay_config["app_id"],
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": self.alipay_config["notify_url"],
            "return_url": self.alipay_config["return_url"],
            "biz_content": json.dumps(biz_content, separators=(',', ':'))
        }

        # 生成签名
        params["sign"] = self._generate_alipay_sign(params)

        # 构建支付URL
        payment_url = f"{gateway}?{urlencode(params)}"

        return {
            "payment_url": payment_url,
            "qr_code_url": None  # 支付宝页面支付不需要二维码
        }

    async def handle_wechat_notify(self, db: Session, notify_data: Dict[str, Any]) -> bool:
        """处理微信支付回调"""

        # 验证签名
        if not self._verify_wechat_sign(notify_data):
            return False

        # 获取订单
        order = db.query(Order).filter(Order.order_id == notify_data["out_trade_no"]).first()
        if not order:
            return False

        # 检查订单状态
        if order.status != OrderStatus.PENDING.value:
            return True  # 已处理，返回成功

        # 验证金额
        if order.final_amount != int(notify_data["total_fee"]):
            return False

        # 更新订单状态
        if notify_data["return_code"] == "SUCCESS" and notify_data["result_code"] == "SUCCESS":
            order.mark_as_paid(notify_data["transaction_id"])
            db.commit()

            # 调用会员服务激活套餐
            from app.services.membership_service import MembershipService
            membership_service = MembershipService()
            await membership_service.purchase_package(
                db, order.user_id, order.package_id, order.payment_method, order.order_id
            )

        return True

    async def handle_alipay_notify(self, db: Session, notify_data: Dict[str, Any]) -> bool:
        """处理支付宝支付回调"""

        # 验证签名
        if not self._verify_alipay_sign(notify_data):
            return False

        # 获取订单
        order = db.query(Order).filter(Order.order_id == notify_data["out_trade_no"]).first()
        if not order:
            return False

        # 检查订单状态
        if order.status != OrderStatus.PENDING.value:
            return True  # 已处理，返回成功

        # 验证金额
        expected_amount = order.final_amount / 100.0  # 转换为元
        if float(notify_data["total_amount"]) != expected_amount:
            return False

        # 更新订单状态
        if notify_data["trade_status"] in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
            order.mark_as_paid(notify_data["trade_no"])
            db.commit()

            # 调用会员服务激活套餐
            from app.services.membership_service import MembershipService
            membership_service = MembershipService()
            await membership_service.purchase_package(
                db, order.user_id, order.package_id, order.payment_method, order.order_id
            )

        return True

    def _generate_nonce_str(self, length: int = 32) -> str:
        """生成随机字符串"""
        import random
        import string
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    def _generate_wechat_sign(self, params: Dict[str, Any]) -> str:
        """生成微信支付签名"""
        # 按参数名ASCII码从小到大排序
        sorted_params = sorted(params.items())

        # 拼接字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if k != "sign" and v])
        sign_str += f"&key={self.wechat_config['api_key']}"

        # MD5加密并转为大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _verify_wechat_sign(self, params: Dict[str, Any]) -> bool:
        """验证微信支付签名"""
        sign = params.pop("sign", None)
        if not sign:
            return False

        generated_sign = self._generate_wechat_sign(params)
        return sign == generated_sign

    def _generate_alipay_sign(self, params: Dict[str, Any]) -> str:
        """生成支付宝签名"""
        import rsa

        # 按参数名ASCII码从小到大排序
        sorted_params = sorted(params.items())

        # 拼接字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if k != "sign" and v])

        # RSA2签名
        private_key = rsa.PrivateKey.load_pkcs1(self.alipay_config["private_key"])
        signature = rsa.sign(sign_str.encode('utf-8'), private_key, 'SHA-256')

        return signature.hex()

    def _verify_alipay_sign(self, params: Dict[str, Any]) -> bool:
        """验证支付宝签名"""
        import rsa

        sign = params.pop("sign", None)
        if not sign:
            return False

        # 按参数名ASCII码从小到大排序
        sorted_params = sorted(params.items())

        # 拼接字符串
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params if k != "sign" and v])

        try:
            public_key = rsa.PublicKey.load_pkcs1_openssl_pem(self.alipay_config["alipay_public_key"])
            rsa.verify(sign_str.encode('utf-8'), bytes.fromhex(sign), public_key)
            return True
        except:
            return False

    def _dict_to_xml(self, params: Dict[str, Any]) -> str:
        """字典转XML"""
        xml = ["<xml>"]
        for k, v in params.items():
            if v:
                xml.append(f"<{k}><![CDATA[{v}]]></{k}>")
        xml.append("</xml>")
        return "".join(xml)

    def _xml_to_dict(self, xml: str) -> Dict[str, Any]:
        """XML转字典"""
        import xml.etree.ElementTree as ET

        result = {}
        root = ET.fromstring(xml)
        for child in root:
            result[child.tag] = child.text
        return result

    async def get_order_status(self, db: Session, order_id: str) -> Dict[str, Any]:
        """获取订单状态"""
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise Exception("订单不存在")

        return {
            "order_id": order.order_id,
            "status": order.status,
            "final_amount": order.final_amount,
            "package_name": order.package_name,
            "created_at": order.created_at.isoformat(),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "expires_at": order.expires_at.isoformat(),
            "is_expired": order.is_expired
        }

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