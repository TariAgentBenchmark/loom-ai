# 从聚合扫码迁移到聚合收银台指南

## 概述

本文档指导您如何从拉卡拉聚合扫码支付迁移到聚合收银台支付。聚合收银台提供了更丰富的支付方式和更好的用户体验。

## 主要变化

### 1. API端点变化

| 聚合扫码 | 聚合收银台 | 说明 |
|----------|------------|------|
| `POST /api/v1/payment/lakala/micropay` | `POST /api/v1/payment/lakala/counter/create` | 创建支付订单 |
| `POST /api/v1/payment/lakala/preorder` | `POST /api/v1/payment/lakala/counter/create` | 创建支付订单 |
| - | `POST /api/v1/payment/lakala/counter/query` | 查询订单状态 |
| - | `POST /api/v1/payment/lakala/counter/close` | 关闭订单 |

### 2. 请求参数变化

**聚合扫码参数:**
```json
{
  "req_data": {
    "merchant_no": "82229007392000A",
    "term_no": "D9296400",
    "total_fee": "1",
    "auth_code": "134648449456456456",
    "out_trade_no": "ORDER123456"
  }
}
```

**聚合收银台参数:**
```json
{
  "out_order_no": "ORDER123456",
  "total_amount": 1,
  "order_info": "测试商品",
  "notify_url": "https://your-domain.com/notify",
  "callback_url": "https://your-domain.com/callback",
  "payment_method": "ALIPAY"
}
```

### 3. 响应格式变化

**聚合扫码响应:**
```json
{
  "code": "000000",
  "msg": "成功",
  "resp_data": {
    "out_trade_no": "ORDER123456",
    "transaction_id": "202411191234567890"
  }
}
```

**聚合收银台响应:**
```json
{
  "code": "000000",
  "msg": "操作成功",
  "resp_data": {
    "out_order_no": "ORDER123456",
    "pay_order_no": "21092211012001970631000488056",
    "counter_url": "https://pay.lakala.com/pay?order=xxx"
  }
}
```

## 迁移步骤

### 步骤1: 更新后端代码

#### 1.1 替换API调用

**之前 (聚合扫码):**
```python
# 使用 micropay
result = await payment_service.create_lakala_micropay(req_data)

# 使用 preorder  
result = await payment_service.create_lakala_preorder(req_data)
```

**现在 (聚合收银台):**
```python
# 使用 counter create
result = await payment_service.create_lakala_counter_order(
    out_order_no="ORDER123456",
    total_amount=100,
    order_info="商品描述",
    notify_url="https://your-domain.com/notify",
    callback_url="https://your-domain.com/callback",
    payment_method="ALIPAY"
)
```

#### 1.2 更新订单状态查询

**之前:**
```python
# 聚合扫码通常不需要单独查询状态
# 状态通过异步通知获取
```

**现在:**
```python
# 可以主动查询订单状态
result = await payment_service.query_lakala_order_status("ORDER123456")
```

#### 1.3 更新订单关闭逻辑

**之前:**
```python
# 聚合扫码通常不支持关闭订单
```

**现在:**
```python
# 可以主动关闭订单
result = await payment_service.close_lakala_order("ORDER123456")
```

### 步骤2: 更新前端代码

#### 2.1 支付流程变化

**之前 (聚合扫码):**
```javascript
// 1. 获取二维码
const response = await createPreorder(orderData);
// 2. 显示二维码给用户扫描
showQRCode(response.data.qr_code);
// 3. 轮询支付状态
pollPaymentStatus(orderNo);
```

**现在 (聚合收银台):**
```javascript
// 1. 创建收银台订单
const response = await createCounterOrder(orderData);
// 2. 重定向到收银台
window.location.href = response.data.counter_url;
// 3. 用户完成支付后跳转回callback_url
```

#### 2.2 支付结果处理

**之前:**
```javascript
// 通过轮询或WebSocket获取支付结果
function pollPaymentStatus(orderNo) {
  setInterval(async () => {
    const status = await getPaymentStatus(orderNo);
    if (status === 'SUCCESS') {
      showSuccess();
    }
  }, 2000);
}
```

**现在:**
```javascript
// 通过callback_url接收支付结果
function handlePaymentCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const status = urlParams.get('status');
  const orderNo = urlParams.get('out_order_no');
  
  if (status === 'SUCCESS') {
    showSuccess(orderNo);
  } else {
    showFailure(orderNo);
  }
}
```

### 步骤3: 更新通知处理

#### 3.1 通知参数变化

**之前 (聚合扫码通知):**
```json
{
  "out_trade_no": "ORDER123456",
  "transaction_id": "202411191234567890",
  "total_fee": "1",
  "time_end": "20241119120135"
}
```

**现在 (聚合收银台通知):**
```json
{
  "out_order_no": "ORDER123456",
  "pay_order_no": "21092211012001970631000488056",
  "order_status": "SUCCESS",
  "total_amount": "100",
  "resp_time": "20241119120135"
}
```

#### 3.2 更新通知处理逻辑

**之前:**
```python
async def handle_micropay_notification(data: dict):
    out_trade_no = data.get("out_trade_no")
    transaction_id = data.get("transaction_id")
    # 更新订单状态
    await update_order_status(out_trade_no, "PAID", transaction_id)
```

**现在:**
```python
async def handle_counter_notification(data: dict):
    out_order_no = data.get("out_order_no")
    pay_order_no = data.get("pay_order_no")
    order_status = data.get("order_status")
    
    status_map = {
        "SUCCESS": "PAID",
        "FAILED": "FAILED", 
        "CLOSED": "CLOSED"
    }
    
    await update_order_status(
        out_order_no, 
        status_map.get(order_status, "PENDING"),
        pay_order_no
    )
```

## 新功能特性

### 1. 多种支付方式
聚合收银台支持更多支付方式：
- 支付宝、微信支付、银联云闪付
- POS刷卡、快捷支付、网银支付
- 花呗分期、京东白条等

### 2. 更好的用户体验
- 统一的支付页面
- 用户自主选择支付方式
- 支持移动端和PC端

### 3. 更丰富的功能
- 订单状态查询
- 订单关闭
- 退款支持
- 重复支付处理

## 注意事项

### 1. 订单号格式
- 聚合收银台使用 `out_order_no` 而不是 `out_trade_no`
- 确保订单号唯一性

### 2. 金额单位
- 聚合收银台金额单位为分
- 聚合扫码金额单位可能不同

### 3. 测试环境
- 使用测试环境进行迁移测试
- 测试所有支付场景
- 验证通知处理逻辑

### 4. 回滚计划
- 准备回滚到聚合扫码的方案
- 监控支付成功率
- 及时处理迁移问题

## 迁移检查清单

- [ ] 更新后端API调用
- [ ] 更新前端支付流程
- [ ] 更新通知处理逻辑
- [ ] 测试所有支付方式
- [ ] 验证订单状态查询
- [ ] 测试订单关闭功能
- [ ] 更新错误处理
- [ ] 更新日志记录
- [ ] 性能测试
- [ ] 生产环境部署

## 支持

如果在迁移过程中遇到问题，请参考：
- [聚合收银台API文档](./lakala_counter_payment.md)
- [拉卡拉官方文档](https://o.lakala.com)
- 联系技术支持