"""Example usage of Lakala Aggregated Payment Gateway."""

import asyncio
import json
from datetime import datetime, timedelta

from app.services.lakala_counter_service import (
    lakala_counter_service,
    PaymentMethods,
    BusinessTypes,
    CardTypes
)


async def example_create_counter_order():
    """Example of creating a payment order in Lakala Aggregated Payment Gateway."""
    
    # Generate unique order number
    out_order_no = f"ORDER{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Set order expiry time (1 hour from now)
    order_efficient_time = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
    
    # Create payment order
    result = lakala_counter_service.create_payment_order(
        out_order_no=out_order_no,
        total_amount=100,  # ¥1.00 in cents
        order_info="测试商品购买",
        notify_url="https://your-domain.com/api/payment/notify",
        callback_url="https://your-domain.com/payment/success",
        payment_method=PaymentMethods.ALIPAY,  # Specify payment method
        order_efficient_time=order_efficient_time,
        support_cancel=0,  # Disable cancel support
        support_refund=1,  # Enable refund support
        support_repeat_pay=1,  # Enable repeat payment
        # Optional: specify payment method using counter_param
        counter_param={
            "pay_mode": PaymentMethods.ALIPAY
        },
        # Optional: restrict business types
        busi_type_param=[
            {
                "busi_type": BusinessTypes.SCPAY,
                "params": {
                    "pay_mode": PaymentMethods.ALIPAY,
                    "crd_flg": CardTypes.DEBIT
                }
            }
        ]
    )
    
    print("=== 创建聚合收银台订单结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == "000000":
        resp_data = result.get("resp_data", {})
        print(f"\n✅ 订单创建成功!")
        print(f"📋 商户订单号: {resp_data.get('out_order_no')}")
        print(f"🔢 平台订单号: {resp_data.get('pay_order_no')}")
        print(f"💰 订单金额: {resp_data.get('total_amount')} 分")
        print(f"🕒 创建时间: {resp_data.get('order_create_time')}")
        print(f"⏰ 过期时间: {resp_data.get('order_efficient_time')}")
        print(f"🔗 收银台地址: {resp_data.get('counter_url')}")
        
        # Redirect user to counter_url for payment
        print(f"\n👉 请重定向用户到收银台地址完成支付")
    else:
        print(f"\n❌ 订单创建失败: {result.get('msg')}")


async def example_query_order_status():
    """Example of querying order status."""
    
    # Replace with your actual order number
    out_order_no = "ORDER20241119120135"
    
    result = lakala_counter_service.query_order_status(out_order_no)
    
    print("=== 查询订单状态结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == "000000":
        print(f"\n✅ 订单状态查询成功")
    else:
        print(f"\n❌ 订单状态查询失败: {result.get('msg')}")


async def example_close_order():
    """Example of closing an order."""
    
    # Replace with your actual order number
    out_order_no = "ORDER20241119120135"
    
    result = lakala_counter_service.close_order(out_order_no)
    
    print("=== 关闭订单结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("code") == "000000":
        print(f"\n✅ 订单关闭成功")
    else:
        print(f"\n❌ 订单关闭失败: {result.get('msg')}")


async def example_with_different_payment_methods():
    """Example showing different payment methods."""
    
    payment_methods = [
        (PaymentMethods.ALIPAY, "支付宝"),
        (PaymentMethods.WECHAT, "微信支付"),
        (PaymentMethods.UNION, "银联云闪付"),
        (PaymentMethods.QUICK_PAY, "快捷支付"),
    ]
    
    for method, description in payment_methods:
        out_order_no = f"ORDER{datetime.now().strftime('%Y%m%d%H%M%S')}_{method}"
        
        result = lakala_counter_service.create_payment_order(
            out_order_no=out_order_no,
            total_amount=100,
            order_info=f"{description}测试订单",
            payment_method=method,
            counter_param={"pay_mode": method}
        )
        
        print(f"\n=== {description} 支付订单创建 ===")
        if result.get("code") == "000000":
            print(f"✅ {description} 订单创建成功")
            print(f"   收银台地址: {result.get('resp_data', {}).get('counter_url')}")
        else:
            print(f"❌ {description} 订单创建失败: {result.get('msg')}")


def handle_payment_notification(notification_data: dict):
    """
    Example of handling payment notification from Lakala.
    
    This function should be called when Lakala sends payment notification
    to your notify_url.
    """
    
    print("=== 收到支付通知 ===")
    print(json.dumps(notification_data, indent=2, ensure_ascii=False))
    
    # Verify signature (important for security)
    # signature = notification_data.get("sign")
    # if not verify_signature(notification_data, signature):
    #     print("❌ 签名验证失败")
    #     return {"code": "SIGNATURE_ERROR", "msg": "Invalid signature"}
    
    # Process payment result
    order_status = notification_data.get("order_status")
    out_order_no = notification_data.get("out_order_no")
    pay_order_no = notification_data.get("pay_order_no")
    total_amount = notification_data.get("total_amount")
    
    if order_status == "SUCCESS":
        print(f"✅ 支付成功: 订单 {out_order_no}, 金额 {total_amount} 分")
        # Update order status in your database
        # mark_order_as_paid(out_order_no, pay_order_no)
    elif order_status == "FAILED":
        print(f"❌ 支付失败: 订单 {out_order_no}")
        # mark_order_as_failed(out_order_no)
    elif order_status == "CLOSED":
        print(f"⚠️ 订单关闭: 订单 {out_order_no}")
        # mark_order_as_closed(out_order_no)
    
    # Always return success response to Lakala
    response = {
        "code": "000000",
        "msg": "Notification received successfully",
        "resp_time": datetime.now().strftime("%Y%m%d%H%M%S")
    }
    
    print("=== 返回给拉卡拉的响应 ===")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    return response


async def main():
    """Run all examples."""
    
    print("🚀 开始拉卡拉聚合收银台示例")
    print("=" * 50)
    
    # Example 1: Create counter order
    await example_create_counter_order()
    
    print("\n" + "=" * 50)
    
    # Example 2: Query order status
    await example_query_order_status()
    
    print("\n" + "=" * 50)
    
    # Example 3: Close order
    await example_close_order()
    
    print("\n" + "=" * 50)
    
    # Example 4: Different payment methods
    await example_with_different_payment_methods()
    
    print("\n" + "=" * 50)
    
    # Example 5: Payment notification handling
    sample_notification = {
        "out_order_no": "ORDER20241119120135",
        "pay_order_no": "21092211012001970631000488056",
        "order_status": "SUCCESS",
        "total_amount": "100",
        "resp_time": datetime.now().strftime("%Y%m%d%H%M%S")
    }
    handle_payment_notification(sample_notification)


if __name__ == "__main__":
    asyncio.run(main())