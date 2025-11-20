"""Payment service exposing Lakala Counter Payment helper methods."""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.services.lakala_counter_service import (
    lakala_counter_service,
    PaymentMethods,
    BusinessTypes,
    CardTypes
)


class PaymentService:
    """Thin wrapper around Lakala Counter Service for FastAPI endpoints."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def create_lakala_counter_order(
        self,
        out_order_no: str,
        total_amount: int,
        order_info: str,
        notify_url: str = None,
        callback_url: str = None,
        payment_method: str = PaymentMethods.ALIPAY,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create payment order in Lakala Aggregated Payment Gateway.
        
        Args:
            out_order_no: Merchant order number
            total_amount: Order amount in cents
            order_info: Order title/description
            notify_url: Payment notification callback URL
            callback_url: Client redirect URL after payment
            payment_method: Payment method (default: ALIPAY)
            **kwargs: Additional parameters
            
        Returns:
            API response dictionary
        """
        
        # Prepare counter_param for payment method
        counter_param = {
            "pay_mode": payment_method
        }
        
        try:
            response = lakala_counter_service.create_payment_order(
                out_order_no=out_order_no,
                total_amount=total_amount,
                order_info=order_info,
                notify_url=notify_url,
                callback_url=callback_url,
                counter_param=counter_param,
                **kwargs
            )
            return response
        except Exception as exc:
            self.logger.error("创建拉卡拉聚合收银台订单失败: %s", exc)
            return {
                "code": "CREATE_ORDER_ERROR",
                "msg": f"创建支付订单失败: {str(exc)}",
                "resp_time": ""
            }

    async def query_lakala_order_status(self, out_order_no: str) -> Dict[str, Any]:
        """
        Query payment order status.
        
        Args:
            out_order_no: Merchant order number
            
        Returns:
            Order status response
        """
        
        try:
            response = lakala_counter_service.query_order_status(out_order_no)
            return response
        except Exception as exc:
            self.logger.error("查询拉卡拉订单状态失败: %s", exc)
            return {
                "code": "QUERY_ORDER_ERROR",
                "msg": f"查询订单状态失败: {str(exc)}",
                "resp_time": ""
            }

    async def close_lakala_order(self, out_order_no: str) -> Dict[str, Any]:
        """
        Close payment order.
        
        Args:
            out_order_no: Merchant order number
            
        Returns:
            Close order response
        """
        
        try:
            response = lakala_counter_service.close_order(out_order_no)
            return response
        except Exception as exc:
            self.logger.error("关闭拉卡拉订单失败: %s", exc)
            return {
                "code": "CLOSE_ORDER_ERROR",
                "msg": f"关闭订单失败: {str(exc)}",
                "resp_time": ""
            }
