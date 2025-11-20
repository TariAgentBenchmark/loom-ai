# 拉卡拉聚合收银台支付API文档

## 概述

本文档描述了如何使用拉卡拉聚合收银台支付API。聚合收银台与之前的聚合扫码不同，它提供一个统一的支付页面，用户可以在该页面选择不同的支付方式完成支付。

## API端点

### 1. 创建聚合收银台订单

**Endpoint:** `POST /api/v1/payment/lakala/counter/create`

**请求参数:**

```json
{
  "out_order_no": "ORDER20241119120135",
  "total_amount": 100,
  "order_info": "测试商品购买",
  "notify_url": "https://your-domain.com/api/payment/notify",
  "callback_url": "https://your-domain.com/payment/success",
  "payment_method": "ALIPAY",
  "vpos_id": "587305941625155584",
  "channel_id": "2021052614391",
  "order_efficient_time": "20241119130135",
  "support_cancel": 0,
  "support_refund": 1,
  "support_repeat_pay": 1
}
```

**参数说明:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| out_order_no | string | 是 | 商户订单号，最大32字符 |
| total_amount | int | 是 | 订单金额，单位：分 |
| order_info | string | 是 | 订单标题，最大64字符 |
| notify_url | string | 否 | 支付结果通知URL |
| callback_url | string | 否 | 支付完成后跳转URL |
| payment_method | string | 否 | 支付方式，默认ALIPAY |
| vpos_id | string | 否 | 交易设备标识 |
| channel_id | string | 否 | 渠道号 |
| order_efficient_time | string | 否 | 订单有效期，格式：yyyyMMddHHmmss |
| support_cancel | int | 否 | 是否支持撤销，0=不支持，1=支持 |
| support_refund | int | 否 | 是否支持退款，0=不支持，1=支持 |
| support_repeat_pay | int | 否 | 是否支持重复支付，0=不支持，1=支持 |

**响应示例:**

```json
{
  "code": "000000",
  "msg": "操作成功",
  "resp_time": "20241119120135",
  "resp_data": {
    "merchant_no": "8222900701106PZ",
    "channel_id": "25",
    "out_order_no": "ORDER20241119120135",
    "order_create_time": "20241119120135",
    "order_efficient_time": "20241119130135",
    "pay_order_no": "21092211012001970631000488056",
    "total_amount": "100",
    "counter_url": "http://q.huijingcai.top/b/pay?merchantNo=8221210594300JY&merchantOrderNo=08F4542EEC6A4497BC419161747A92FQ&payOrderNo=21092211012001970631000488056"
  }
}
```

### 2. 查询订单状态

**Endpoint:** `POST /api/v1/payment/lakala/counter/query`

**请求参数:**

```json
{
  "out_order_no": "ORDER20241119120135"
}
```

**响应示例:**

```json
{
  "code": "000000",
  "msg": "操作成功",
  "resp_time": "20241119120135",
  "resp_data": {
    "out_order_no": "ORDER20241119120135",
    "order_status": "SUCCESS",
    "total_amount": "100",
    "pay_order_no": "21092211012001970631000488056"
  }
}
```

### 3. 关闭订单

**Endpoint:** `POST /api/v1/payment/lakala/counter/close`

**请求参数:**

```json
{
  "out_order_no": "ORDER20241119120135"
}
```

**响应示例:**

```json
{
  "code": "000000",
  "msg": "操作成功",
  "resp_time": "20241119120135"
}
```

## 支付方式

支持以下支付方式：

| 支付方式 | 代码 | 说明 |
|----------|------|------|
| 支付宝 | ALIPAY | 支付宝支付 |
| 微信支付 | WECHAT | 微信支付 |
| 银联云闪付 | UNION | 银联云闪付 |
| POS刷卡 | CARD | POS刷卡交易 |
| 线上转账 | LKLAT | 线上转账 |
| 快捷支付 | QUICK_PAY | 快捷支付 |
| 网银支付 | EBANK | 网银支付 |
| 银联支付 | UNION_CC | 银联支付 |
| 翼支付 | BESTPAY | 翼支付 |
| 花呗分期 | HB_FQ | 花呗分期 |
| 银联聚分期 | UNION_FQ | 银联聚分期 |
| 线上外卡 | ONLINE_CARDLESS | 线上外卡支付 |
| 京东白条 | JDBT | 京东白条 |
| 支付宝香港钱包 | ALIPAY_HK | 支付宝香港钱包支付 |

## 前端集成示例

### 1. 创建支付订单

```javascript
// 创建支付订单
async function createPaymentOrder() {
  try {
    const response = await fetch('/api/v1/payment/lakala/counter/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        out_order_no: `ORDER${Date.now()}`,
        total_amount: 100, // ¥1.00
        order_info: '测试商品购买',
        notify_url: 'https://your-domain.com/api/payment/notify',
        callback_url: 'https://your-domain.com/payment/success',
        payment_method: 'ALIPAY'
      })
    });

    const result = await response.json();
    
    if (result.code === '000000') {
      // 重定向到收银台页面
      window.location.href = result.data.counter_url;
    } else {
      console.error('创建订单失败:', result.msg);
    }
  } catch (error) {
    console.error('请求失败:', error);
  }
}
```

### 2. 处理支付回调

```javascript
// 支付成功回调页面
function handlePaymentCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const orderNo = urlParams.get('out_order_no');
  const status = urlParams.get('status');
  
  if (status === 'SUCCESS') {
    // 显示支付成功页面
    showSuccessPage(orderNo);
  } else {
    // 显示支付失败页面
    showFailurePage(orderNo);
  }
}
```

### 3. 轮询订单状态

```javascript
// 轮询订单状态
async function pollOrderStatus(orderNo) {
  const maxAttempts = 30; // 最大尝试次数
  const interval = 2000; // 2秒间隔
  
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch('/api/v1/payment/lakala/counter/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ out_order_no: orderNo })
      });
      
      const result = await response.json();
      
      if (result.code === '000000') {
        const status = result.data.order_status;
        
        if (status === 'SUCCESS') {
          // 支付成功
          return { success: true, data: result.data };
        } else if (status === 'FAILED' || status === 'CLOSED') {
          // 支付失败或订单关闭
          return { success: false, error: `支付失败: ${status}` };
        }
        // 继续轮询
      }
    } catch (error) {
      console.error('查询订单状态失败:', error);
    }
    
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  return { success: false, error: '支付超时' };
}
```

## 支付通知处理

当用户完成支付后，拉卡拉会向你的 `notify_url` 发送支付结果通知。你需要处理这些通知并更新订单状态。

### 通知参数示例

```json
{
  "out_order_no": "ORDER20241119120135",
  "pay_order_no": "21092211012001970631000488056",
  "order_status": "SUCCESS",
  "total_amount": "100",
  "resp_time": "20241119120135"
}
```

### 通知处理响应

收到通知后，你需要返回以下格式的响应：

```json
{
  "code": "000000",
  "msg": "Notification received successfully",
  "resp_time": "20241119120135"
}
```

## 错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 000000 | 成功 | 操作成功 |
| 其他错误码 | 具体错误信息 | 根据错误信息进行相应处理 |

## 注意事项

1. **订单号唯一性**: 确保每个订单的 `out_order_no` 是唯一的
2. **金额单位**: 金额单位为分，100分 = ¥1.00
3. **时间格式**: 所有时间字段使用 `yyyyMMddHHmmss` 格式
4. **签名验证**: 生产环境务必验证请求和响应的签名
5. **通知处理**: 及时处理支付通知并返回成功响应
6. **测试环境**: 开发阶段使用测试环境，生产环境切换URL

## 与聚合扫码的区别

| 特性 | 聚合扫码 | 聚合收银台 |
|------|----------|------------|
| 支付方式 | 扫码支付 | 多种支付方式 |
| 用户体验 | 用户扫码支付 | 用户进入收银台选择支付方式 |
| 集成复杂度 | 较低 | 较高 |
| 适用场景 | 线下扫码 | 线上支付、多种支付方式场景 |