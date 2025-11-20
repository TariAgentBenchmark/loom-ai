"""Test script for Lakala Aggregated Payment Gateway."""

import asyncio
import json
from datetime import datetime, timedelta

from app.services.lakala_counter_service import (
    lakala_counter_service,
    PaymentMethods
)


async def test_create_counter_order():
    """Test creating a counter payment order."""
    print("🧪 Testing create counter order...")
    
    out_order_no = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
    order_efficient_time = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
    
    result = lakala_counter_service.create_payment_order(
        out_order_no=out_order_no,
        total_amount=1,  # Test with 1 cent to avoid real charges
        order_info="测试订单",
        order_efficient_time=order_efficient_time,
        counter_param={"pay_mode": PaymentMethods.ALIPAY}
    )
    
    print(f"📋 Request Order No: {out_order_no}")
    print(f"📦 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") == "000000":
        print("✅ Create counter order test PASSED")
        return out_order_no
    else:
        print(f"❌ Create counter order test FAILED: {result.get('msg')}")
        return None


async def test_query_order_status(order_no: str):
    """Test querying order status."""
    print(f"\n🧪 Testing query order status for {order_no}...")
    
    result = lakala_counter_service.query_order_status(order_no)
    
    print(f"📦 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") in ["000000", "ORDER_NOT_FOUND"]:
        print("✅ Query order status test PASSED")
        return True
    else:
        print(f"❌ Query order status test FAILED: {result.get('msg')}")
        return False


async def test_close_order(order_no: str):
    """Test closing an order."""
    print(f"\n🧪 Testing close order for {order_no}...")
    
    result = lakala_counter_service.close_order(order_no)
    
    print(f"📦 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("code") in ["000000", "ORDER_ALREADY_CLOSED"]:
        print("✅ Close order test PASSED")
        return True
    else:
        print(f"❌ Close order test FAILED: {result.get('msg')}")
        return False


async def test_payment_methods():
    """Test different payment methods."""
    print("\n🧪 Testing different payment methods...")
    
    payment_methods = [
        (PaymentMethods.ALIPAY, "支付宝"),
        (PaymentMethods.WECHAT, "微信支付"),
        (PaymentMethods.UNION, "银联云闪付"),
    ]
    
    for method, description in payment_methods:
        out_order_no = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}_{method}"
        
        result = lakala_counter_service.create_payment_order(
            out_order_no=out_order_no,
            total_amount=1,
            order_info=f"{description}测试",
            counter_param={"pay_mode": method}
        )
        
        if result.get("code") == "000000":
            print(f"✅ {description} payment method test PASSED")
        else:
            print(f"❌ {description} payment method test FAILED: {result.get('msg')}")


async def test_error_cases():
    """Test error cases."""
    print("\n🧪 Testing error cases...")
    
    # Test with missing required field
    result = lakala_counter_service.create_payment_order(
        out_order_no="",  # Empty order number
        total_amount=100,
        order_info="测试订单"
    )
    
    print(f"📦 Empty order number response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Test with invalid amount
    result = lakala_counter_service.create_payment_order(
        out_order_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
        total_amount=0,  # Invalid amount
        order_info="测试订单"
    )
    
    print(f"📦 Invalid amount response: {json.dumps(result, indent=2, ensure_ascii=False)}")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Lakala Counter Payment Gateway Tests")
    print("=" * 60)
    
    # Test 1: Create counter order
    order_no = await test_create_counter_order()
    
    if order_no:
        # Test 2: Query order status
        await test_query_order_status(order_no)
        
        # Test 3: Close order
        await test_close_order(order_no)
    
    # Test 4: Different payment methods
    await test_payment_methods()
    
    # Test 5: Error cases
    await test_error_cases()
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")


if __name__ == "__main__":
    # Note: These tests require proper Lakala API credentials
    # Make sure to set up your .env file with correct credentials
    asyncio.run(run_all_tests())