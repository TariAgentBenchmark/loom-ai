"""Lakala Aggregated Payment Gateway Service for counter payments."""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.services.lakala_api import LakalaApiClient
from app.core.config import settings


class LakalaCounterService:
    """Service for Lakala Aggregated Payment Gateway operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = LakalaApiClient()
    
    def create_payment_order(
        self,
        out_order_no: str,
        total_amount: int,
        order_info: str,
        notify_url: Optional[str] = None,
        callback_url: Optional[str] = None,
        vpos_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        order_efficient_time: Optional[str] = None,
        support_cancel: int = 0,
        support_refund: int = 1,
        support_repeat_pay: int = 1,
        counter_param: Optional[Dict] = None,
        busi_type_param: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        Create a payment order in Lakala Aggregated Payment Gateway.
        
        Args:
            out_order_no: Merchant order number (max 32 chars)
            total_amount: Order amount in cents (e.g., 100 = ¥1.00)
            order_info: Order title/description (max 64 chars)
            notify_url: Payment notification callback URL
            callback_url: Client redirect URL after payment
            vpos_id: Transaction device identifier
            channel_id: Channel number
            order_efficient_time: Order expiry time (yyyyMMddHHmmss)
            support_cancel: Enable cancel support (0=no, 1=yes)
            support_refund: Enable refund support (0=no, 1=yes)
            support_repeat_pay: Enable repeat payment (0=no, 1=yes)
            counter_param: Payment method parameters
            busi_type_param: Business type control parameters
            **kwargs: Additional optional parameters
            
        Returns:
            API response dictionary
        """
        # Set default expiry time (current time + 1 hour)
        if not order_efficient_time:
            expiry_time = datetime.now() + timedelta(hours=9)
            order_efficient_time = expiry_time.strftime("%Y%m%d%H%M%S")
        
        # Prepare request data
        req_data = {
            "out_order_no": out_order_no,
            "merchant_no": settings.lakala_merchant_no,
            "total_amount": str(total_amount),
            "order_efficient_time": order_efficient_time,
            "order_info": order_info,
            "support_cancel": str(support_cancel),
            "support_refund": str(support_refund),
            "support_repeat_pay": str(support_repeat_pay),
        }
        
        # Add optional parameters
        if notify_url:
            req_data["notify_url"] = notify_url
        if callback_url:
            req_data["callback_url"] = callback_url
        if vpos_id:
            req_data["vpos_id"] = vpos_id
        if channel_id:
            req_data["channel_id"] = channel_id
        
        # Add counter_param for specific payment methods
        if counter_param:
            req_data["counter_param"] = json.dumps(counter_param, ensure_ascii=False)
        
        # Add busi_type_param for business type control
        if busi_type_param:
            req_data["busi_type_param"] = json.dumps(busi_type_param, ensure_ascii=False)
        
        # Add other optional parameters
        for key, value in kwargs.items():
            if value is not None:
                req_data[key] = value
        
        try:
            response = self.client.create_counter_order(req_data)
            self.logger.info("Payment order created successfully: %s", out_order_no)
            return response
        except Exception as e:
            self.logger.error("Failed to create payment order %s: %s", out_order_no, str(e))
            return {
                "code": "CREATE_ORDER_ERROR",
                "msg": f"Failed to create payment order: {str(e)}",
                "resp_time": datetime.now().strftime("%Y%m%d%H%M%S")
            }
    
    def query_order_status(self, out_order_no: str) -> Dict:
        """
        Query payment order status.
        
        Args:
            out_order_no: Merchant order number
            
        Returns:
            Order status response
        """
        req_data = {
            "out_order_no": out_order_no,
            "merchant_no": settings.lakala_merchant_no,
        }
        
        try:
            response = self.client.query_counter_order(req_data)
            return response
        except Exception as e:
            self.logger.error("Failed to query order status %s: %s", out_order_no, str(e))
            return {
                "code": "QUERY_ORDER_ERROR",
                "msg": f"Failed to query order status: {str(e)}",
                "resp_time": datetime.now().strftime("%Y%m%d%H%M%S")
            }
    
    def close_order(self, out_order_no: str) -> Dict:
        """
        Close payment order.
        
        Args:
            out_order_no: Merchant order number
            
        Returns:
            Close order response
        """
        req_data = {
            "out_order_no": out_order_no,
            "merchant_no": settings.lakala_merchant_no,
        }
        
        try:
            response = self.client.close_counter_order(req_data)
            return response
        except Exception as e:
            self.logger.error("Failed to close order %s: %s", out_order_no, str(e))
            return {
                "code": "CLOSE_ORDER_ERROR",
                "msg": f"Failed to close order: {str(e)}",
                "resp_time": datetime.now().strftime("%Y%m%d%H%M%S")
            }


# Payment method constants
class PaymentMethods:
    """Supported payment methods for counter_param."""
    ALIPAY = "ALIPAY"  # 支付宝
    WECHAT = "WECHAT"  # 微信支付
    UNION = "UNION"    # 银联云闪付
    CARD = "CARD"      # POS刷卡交易
    LKLAT = "LKLAT"    # 线上转帐
    QUICK_PAY = "QUICK_PAY"  # 快捷支付
    EBANK = "EBANK"    # 网银支付
    UNION_CC = "UNION_CC"  # 银联支付
    BESTPAY = "BESTPAY"  # 翼支付
    HB_FQ = "HB_FQ"    # 花呗分期
    UNION_FQ = "UNION_FQ"  # 银联聚分期
    ONLINE_CARDLESS = "ONLINE_CARDLESS"  # 线上外卡
    JDBT = "JDBT"      # 京东白条
    ALIPAY_HK = "ALIPAY_HK"  # 支付宝香港钱包支付


# Business type constants for busi_type_param
class BusinessTypes:
    """Business type constants for busi_type_param."""
    UPCARD = "UPCARD"  # 刷卡
    SCPAY = "SCPAY"    # 扫码


# Card type constants
class CardTypes:
    """Card type constants for busi_type_param."""
    DEBIT = "CRDFLG_D"      # 借记卡
    CREDIT = "CRDFLG_C"     # 贷记卡
    OTHER = "CRDFLG_OTH"    # 不明确是借记卡还是贷记卡


# Create global service instance
lakala_counter_service = LakalaCounterService()