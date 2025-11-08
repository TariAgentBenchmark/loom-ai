# 套餐充值 API

## 概述

套餐充值模块负责处理用户的会员套餐购买、算力充值、支付管理等功能。

## 接口列表

### 1. 获取套餐列表

**接口地址**: `GET /payment/packages`

**描述**: 获取所有可用的套餐信息

**查询参数**:
- `type`: 套餐类型（可选）
  - `membership`: 会员套餐
  - `credits`: 算力充值
  - `all`: 全部（默认）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "membership": {
      "monthly": [
        {
          "packageId": "monthly_trial",
          "name": "试用体验",
          "type": "monthly",
          "price": 0,
          "originalPrice": 0,
          "credits": 200,
          "duration": 7,            // 天数
          "features": [
            "赠送200算力积分",
            "7天内有效",
            "循环图案处理",
            "线条/矢量提取",
            "高清放大",
            "毛线刺绣增强"
          ],
          "popular": false
        },
        {
          "packageId": "monthly_light",
          "name": "轻享版",
          "type": "monthly",
          "price": 2900,            // 价格（分）
          "originalPrice": 4900,
          "credits": 3000,
          "duration": 30,
          "features": [
            "每月3000算力积分",
            "AI应用高速队列",
            "循环图案处理",
            "线条/矢量提取",
            "高清放大",
            "矢量风格转换(会员专享)",
            "毛线刺绣增强"
          ],
          "popular": true,
          "discount": "限时优惠"
        },
        {
          "packageId": "monthly_basic",
          "name": "基础版",
          "type": "monthly",
          "price": 6900,
          "originalPrice": 8900,
          "credits": 7500,
          "duration": 30,
          "features": [
            "每月7500算力积分",
            "AI应用高速队列",
            "循环图案处理",
            "线条/矢量提取",
            "矢量风格转换(会员专享)",
            "高清放大",
            "优先处理队列",
            "毛线刺绣增强"
          ],
          "popular": false,
          "discount": "限时优惠"
        },
        {
          "packageId": "monthly_premium",
          "name": "高级版",
          "type": "monthly",
          "price": 9900,
          "originalPrice": 14900,
          "credits": 11000,
          "duration": 30,
          "features": [
            "每月11000算力积分",
            "AI应用高速队列",
            "循环图案处理",
            "线条/矢量提取",
            "矢量风格转换(会员专享)",
            "进一步处理(会员专享)",
            "高清放大",
            "超级高速队列",
            "自定义处理指令",
            "毛线刺绣增强"
          ],
          "popular": false,
          "discount": "限时优惠"
        }
      ],
      "quarterly": [
        {
          "packageId": "quarterly_light",
          "name": "轻享季度版",
          "type": "quarterly",
          "price": 7900,
          "originalPrice": 12900,
          "credits": 8000,
          "duration": 90,
          "features": [
            "每月8000算力积分",
            "所有基础功能",
            "矢量风格转换"
          ],
          "popular": false,
          "discount": "季度优惠"
        }
      ],
      "yearly": [
        {
          "packageId": "yearly_standard",
          "name": "标准年费版",
          "type": "yearly",
          "price": 29900,
          "originalPrice": 58800,
          "credits": 10000,
          "duration": 365,
          "features": [
            "每月10000算力积分",
            "全功能访问",
            "年费专享特权"
          ],
          "popular": false,
          "discount": "超值年费"
        }
      ]
    },
    "credits": [
      {
        "packageId": "credits_basic",
        "name": "基础算力包",
        "type": "credits",
        "price": 1900,
        "credits": 1000,
        "description": "适合偶尔使用",
        "popular": false
      },
      {
        "packageId": "credits_standard",
        "name": "标准算力包",
        "type": "credits",
        "price": 4900,
        "credits": 3000,
        "description": "性价比最高",
        "popular": true
      },
      {
        "packageId": "credits_professional",
        "name": "专业算力包",
        "type": "credits",
        "price": 9900,
        "credits": 7000,
        "description": "适合专业用户",
        "popular": false
      },
      {
        "packageId": "credits_enterprise",
        "name": "企业算力包",
        "type": "credits",
        "price": 19900,
        "credits": 15000,
        "description": "企业团队首选",
        "popular": false
      }
    ]
  },
  "message": "获取套餐列表成功"
}
```

### 2. 创建订单

**接口地址**: `POST /payment/orders`

**描述**: 创建支付订单

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "packageId": "monthly_basic",     // 套餐ID（必填）
  "paymentMethod": "alipay",        // 支付方式（必填）
  "quantity": 1,                    // 购买数量（默认1）
  "couponCode": "NEWUSER10"         // 优惠券码（可选）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "orderId": "order_123456789",
    "packageId": "monthly_basic",
    "packageName": "基础版",
    "originalAmount": 8900,         // 原价（分）
    "discountAmount": 2000,         // 折扣金额
    "finalAmount": 6900,            // 实付金额
    "paymentMethod": "alipay",
    "status": "pending",            // 订单状态
    "paymentUrl": "https://pay.loom-ai.com/pay/order_123456789",
    "qrCode": "https://api.loom-ai.com/payment/qr/order_123456789.png",
    "expiresAt": "2023-12-01T11:00:00Z", // 订单过期时间
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "订单创建成功"
}
```

### 3. 查询订单状态

**接口地址**: `GET /payment/orders/{orderId}`

**描述**: 查询指定订单的状态

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `orderId`: 订单ID

**响应示例**:
```json
{
  "success": true,
  "data": {
    "orderId": "order_123456789",
    "packageId": "monthly_basic",
    "packageName": "基础版",
    "amount": 6900,
    "paymentMethod": "alipay",
    "status": "paid",               // 订单状态：pending|paid|failed|cancelled|refunded
    "paidAt": "2023-12-01T10:05:00Z",
    "transactionId": "txn_alipay_987654321",
    "invoice": {
      "available": true,
      "downloadUrl": "https://api.loom-ai.com/payment/invoice/order_123456789.pdf"
    },
    "createdAt": "2023-12-01T10:00:00Z"
  },
  "message": "查询订单成功"
}
```

### 4. 获取订单列表

**接口地址**: `GET /payment/orders`

**描述**: 获取用户的订单列表

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `status`: 订单状态过滤（可选）
- `type`: 订单类型过滤（membership|credits）（可选）
- `startDate`: 开始日期 (YYYY-MM-DD)
- `endDate`: 结束日期 (YYYY-MM-DD)
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "orderId": "order_123456789",
        "packageName": "基础版",
        "type": "membership",
        "amount": 6900,
        "status": "paid",
        "paymentMethod": "alipay",
        "createdAt": "2023-12-01T10:00:00Z",
        "paidAt": "2023-12-01T10:05:00Z"
      }
    ],
    "summary": {
      "totalOrders": 12,
      "totalAmount": 82800,          // 总金额（分）
      "paidOrders": 10,
      "pendingOrders": 1,
      "failedOrders": 1
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 12,
      "totalPages": 1
    }
  },
  "message": "获取订单列表成功"
}
```

### 5. 取消订单

**接口地址**: `POST /payment/orders/{orderId}/cancel`

**描述**: 取消待支付的订单

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `orderId`: 订单ID

**请求参数**:
```json
{
  "reason": "不需要了"            // 取消原因（可选）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "orderId": "order_123456789",
    "status": "cancelled",
    "cancelledAt": "2023-12-01T10:30:00Z"
  },
  "message": "订单取消成功"
}
```

### 6. 申请退款

**接口地址**: `POST /payment/refunds`

**描述**: 申请订单退款

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "orderId": "order_123456789",    // 订单ID（必填）
  "reason": "产品不符合预期",       // 退款原因（必填）
  "amount": 6900,                  // 退款金额（可选，默认全额）
  "description": "详细说明..."     // 详细说明（可选）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "refundId": "refund_123456789",
    "orderId": "order_123456789",
    "amount": 6900,
    "reason": "产品不符合预期",
    "status": "processing",         // 退款状态：processing|approved|rejected|completed
    "estimatedTime": "3-5个工作日",
    "createdAt": "2023-12-01T10:45:00Z"
  },
  "message": "退款申请提交成功"
}
```

### 7. 获取退款记录

**接口地址**: `GET /payment/refunds`

**描述**: 获取用户的退款记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `status`: 退款状态过滤（可选）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "refunds": [
      {
        "refundId": "refund_123456789",
        "orderId": "order_123456789",
        "packageName": "基础版",
        "amount": 6900,
        "reason": "产品不符合预期",
        "status": "completed",
        "createdAt": "2023-12-01T10:45:00Z",
        "completedAt": "2023-12-03T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 2,
      "totalPages": 1
    }
  },
  "message": "获取退款记录成功"
}
```

### 8. 获取支付方式

**接口地址**: `GET /payment/methods`

**描述**: 获取可用的支付方式列表

**响应示例**:
```json
{
  "success": true,
  "data": {
    "methods": [
      {
        "code": "alipay",
        "name": "支付宝",
        "icon": "https://cdn.loom-ai.com/icons/alipay.png",
        "description": "支持支付宝扫码支付",
        "enabled": true,
        "fees": 0                   // 手续费（分）
      },
      {
        "code": "wechat",
        "name": "微信支付",
        "icon": "https://cdn.loom-ai.com/icons/wechat.png",
        "description": "支持微信扫码支付",
        "enabled": true,
        "fees": 0
      },
      {
        "code": "bank_card",
        "name": "银行卡",
        "icon": "https://cdn.loom-ai.com/icons/bank.png",
        "description": "支持储蓄卡和信用卡",
        "enabled": true,
        "fees": 0
      }
    ]
  },
  "message": "获取支付方式成功"
}
```

### 9. 获取优惠券

**接口地址**: `GET /payment/coupons`

**描述**: 获取用户可用的优惠券

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `packageId`: 适用的套餐ID（可选）
- `status`: 优惠券状态（available|used|expired）（可选）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "coupons": [
      {
        "couponId": "coupon_123456789",
        "code": "NEWUSER10",
        "name": "新用户10元优惠券",
        "type": "amount",           // 类型：amount|percentage
        "value": 1000,              // 优惠值（金额类型为分，折扣类型为百分比*100）
        "minAmount": 5000,          // 最低消费金额
        "applicablePackages": ["monthly_basic", "monthly_premium"],
        "status": "available",
        "expiresAt": "2023-12-31T23:59:59Z",
        "createdAt": "2023-12-01T00:00:00Z"
      }
    ]
  },
  "message": "获取优惠券成功"
}
```

### 10. 验证优惠券

**接口地址**: `POST /payment/coupons/validate`

**描述**: 验证优惠券是否可用

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "couponCode": "NEWUSER10",       // 优惠券码（必填）
  "packageId": "monthly_basic"     // 套餐ID（必填）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "valid": true,
    "couponId": "coupon_123456789",
    "name": "新用户10元优惠券",
    "discountAmount": 1000,         // 优惠金额（分）
    "finalAmount": 5900,            // 使用优惠券后的价格
    "conditions": "满50元可用"
  },
  "message": "优惠券验证成功"
}
```

### 11. 下载发票

**接口地址**: `GET /payment/invoice/{orderId}`

**描述**: 下载订单发票

**请求头**:
```
Authorization: Bearer access-token-here
```

**路径参数**:
- `orderId`: 订单ID

**查询参数**:
- `format`: 发票格式（pdf|image）（默认pdf）

**响应**: 直接返回发票文件流

## 支付流程说明

### 标准支付流程

1. **选择套餐** → 调用 `GET /payment/packages` 获取套餐列表
2. **创建订单** → 调用 `POST /payment/orders` 创建支付订单
3. **完成支付** → 用户通过返回的支付链接完成支付
4. **查询结果** → 调用 `GET /payment/orders/{orderId}` 确认支付结果
5. **自动生效** → 支付成功后系统自动为用户开通服务

### 支付状态流转

```
pending → paid → completed
    ↓
cancelled
    ↓
refunded
```

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| PAY001 | 套餐不存在 |
| PAY002 | 支付方式不支持 |
| PAY003 | 订单已支付 |
| PAY004 | 订单不存在 |
| PAY005 | 订单已过期 |
| PAY006 | 优惠券不存在 |
| PAY007 | 优惠券已过期 |
| PAY008 | 优惠券不适用当前套餐 |
| PAY009 | 退款申请已存在 |
| PAY010 | 该订单不支持退款 |
| PAY011 | 支付失败 |
| PAY012 | 发票不存在 |
