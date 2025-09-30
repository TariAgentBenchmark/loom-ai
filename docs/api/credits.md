# 算力管理 API

## 概述

算力管理模块负责用户算力的查询、充值、消耗记录等功能。

## 接口列表

### 1. 获取算力余额

**接口地址**: `GET /credits/balance`

**描述**: 获取用户当前算力余额

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "credits": 2580,             // 当前算力余额
    "monthlyUsage": 1840,        // 本月已用算力
    "monthlyQuota": 11000,       // 本月配额（会员）
    "remainingQuota": 9160,      // 本月剩余配额
    "usagePercentage": 16.7,     // 使用百分比
    "lastUpdated": "2023-12-01T10:00:00Z"
  },
  "message": "获取算力余额成功"
}
```

### 2. 获取算力消耗记录

**接口地址**: `GET /credits/transactions`

**描述**: 获取算力的充值和消耗记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `type`: 交易类型（可选）
  - `earn`: 获得算力（充值、赠送等）
  - `spend`: 消耗算力（处理任务）
  - `all`: 全部（默认）
- `startDate`: 开始日期 (YYYY-MM-DD)
- `endDate`: 结束日期 (YYYY-MM-DD)
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "transactionId": "txn_123456789",
        "type": "spend",            // 类型：earn|spend
        "amount": -60,              // 算力变动（负数为消耗）
        "balance": 2580,            // 交易后余额
        "description": "AI四方连续转换",
        "relatedTaskId": "task_seamless_123456789",
        "createdAt": "2023-12-01T10:00:00Z"
      },
      {
        "transactionId": "txn_123456788",
        "type": "earn",
        "amount": 3000,
        "balance": 2640,
        "description": "基础版月度充值",
        "relatedOrderId": "order_987654321",
        "createdAt": "2023-11-01T09:00:00Z"
      }
    ],
    "summary": {
      "totalEarned": 15000,       // 总获得算力
      "totalSpent": 12420,        // 总消耗算力
      "netChange": 2580,          // 净变化
      "period": "2023-11-01 to 2023-12-01"
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 247,
      "totalPages": 13
    }
  },
  "message": "获取交易记录成功"
}
```

### 3. 预估算力消耗

**接口地址**: `POST /credits/estimate`

**描述**: 预估指定操作的算力消耗

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "type": "seamless",           // 处理类型（必填）
  "options": {                  // 处理选项（可选）
    "removeBackground": true,
    "seamlessLoop": true
  },
  "imageInfo": {               // 图片信息（可选，用于更精确预估）
    "width": 1024,
    "height": 1024,
    "fileSize": 2048576
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "estimatedCredits": 60,      // 预估算力消耗
    "baseCredits": 60,           // 基础算力
    "additionalCredits": 0,      // 附加算力（高分辨率等）
    "discount": 0,               // 会员折扣
    "finalCredits": 60,          // 最终消耗算力
    "canAfford": true,           // 是否有足够算力
    "currentBalance": 2580       // 当前余额
  },
  "message": "预估算力消耗成功"
}
```

### 4. 获取算力价格表

**接口地址**: `GET /credits/pricing`

**描述**: 获取各种处理功能的算力价格

**响应示例**:
```json
{
  "success": true,
  "data": {
    "processing": {
      "seamless": {
        "name": "AI四方连续转换",
        "baseCredits": 60,
        "description": "对独幅矩形图转换成可四方连续的打印图"
      },
      "vectorize": {
        "name": "AI矢量化(转SVG)",
        "baseCredits": 100,
        "description": "使用AI一键将图片变成矢量图"
      },
      "extractEdit": {
        "name": "AI提取编辑",
        "baseCredits": 80,
        "description": "使用AI提取和编辑图片内容"
      },
      "extractPattern": {
        "name": "AI提取花型",
        "baseCredits": 100,
        "description": "提取图案中的花型元素"
      },
      "removeWatermark": {
        "name": "AI智能去水印",
        "baseCredits": 70,
        "description": "去除文字和Logo水印"
      },
      "denoise": {
        "name": "AI布纹去噪",
        "baseCredits": 80,
        "description": "去除噪点和布纹"
      },
      "embroidery": {
        "name": "AI毛线刺绣增强",
        "baseCredits": 90,
        "description": "毛线刺绣效果处理"
      }
    },
    "modifiers": {
      "highResolution": {
        "threshold": 2048,        // 触发条件：分辨率超过2048px
        "multiplier": 1.5,        // 算力倍数
        "description": "高分辨率处理"
      },
      "largeFile": {
        "threshold": 10485760,    // 触发条件：文件超过10MB
        "additionalCredits": 20,  // 额外算力
        "description": "大文件处理"
      }
    },
    "discounts": {
      "premium": {
        "membershipType": "premium",
        "discount": 0.1,          // 10%折扣
        "description": "高级会员折扣"
      },
      "enterprise": {
        "membershipType": "enterprise", 
        "discount": 0.2,          // 20%折扣
        "description": "企业会员折扣"
      }
    },
    "lastUpdated": "2023-12-01T00:00:00Z"
  },
  "message": "获取价格表成功"
}
```

### 5. 获取算力统计

**接口地址**: `GET /credits/statistics`

**描述**: 获取算力使用统计信息

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `period`: 统计周期
  - `daily`: 日统计（最近30天）
  - `weekly`: 周统计（最近12周）
  - `monthly`: 月统计（最近12个月）
  - `yearly`: 年统计

**响应示例**:
```json
{
  "success": true,
  "data": {
    "period": "daily",
    "statistics": [
      {
        "date": "2023-12-01",
        "earned": 0,              // 当日获得算力
        "spent": 340,             // 当日消耗算力
        "balance": 2580,          // 当日结束余额
        "tasks": 6                // 当日处理任务数
      },
      {
        "date": "2023-11-30",
        "earned": 0,
        "spent": 180,
        "balance": 2920,
        "tasks": 3
      }
    ],
    "summary": {
      "totalEarned": 3000,        // 期间总获得
      "totalSpent": 2420,         // 期间总消耗
      "averageDaily": 80.7,       // 日均消耗
      "totalTasks": 156,          // 总任务数
      "period": "最近30天"
    }
  },
  "message": "获取统计信息成功"
}
```

### 6. 算力预警设置

**接口地址**: `GET /credits/alerts`

**描述**: 获取算力预警设置

**请求头**:
```
Authorization: Bearer access-token-here
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "lowBalanceAlert": {
      "enabled": true,
      "threshold": 200,           // 预警阈值
      "notificationMethods": ["email", "push"]
    },
    "monthlyUsageAlert": {
      "enabled": true,
      "threshold": 0.8,          // 80%使用率预警
      "notificationMethods": ["email"]
    },
    "membershipExpiryAlert": {
      "enabled": true,
      "advanceDays": 7,          // 提前7天预警
      "notificationMethods": ["email", "sms"]
    }
  },
  "message": "获取预警设置成功"
}
```

### 7. 更新预警设置

**接口地址**: `PUT /credits/alerts`

**描述**: 更新算力预警设置

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "lowBalanceAlert": {
    "enabled": true,
    "threshold": 300,
    "notificationMethods": ["email", "push"]
  },
  "monthlyUsageAlert": {
    "enabled": true,
    "threshold": 0.9,
    "notificationMethods": ["email"]
  },
  "membershipExpiryAlert": {
    "enabled": true,
    "advanceDays": 5,
    "notificationMethods": ["email", "sms"]
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "updatedAt": "2023-12-01T10:30:00Z"
  },
  "message": "预警设置更新成功"
}
```

### 8. 算力转赠

**接口地址**: `POST /credits/transfer`

**描述**: 将算力转赠给其他用户

**请求头**:
```
Authorization: Bearer access-token-here
```

**请求参数**:
```json
{
  "recipientEmail": "friend@example.com", // 接收方邮箱（必填）
  "amount": 100,                         // 转赠数量（必填）
  "message": "送给你的算力，祝使用愉快！"    // 转赠留言（可选）
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "transferId": "transfer_123456789",
    "amount": 100,
    "recipientEmail": "friend@example.com",
    "senderBalance": 2480,              // 转赠后余额
    "status": "completed",
    "createdAt": "2023-12-01T10:35:00Z"
  },
  "message": "算力转赠成功"
}
```

### 9. 获取转赠记录

**接口地址**: `GET /credits/transfers`

**描述**: 获取算力转赠记录

**请求头**:
```
Authorization: Bearer access-token-here
```

**查询参数**:
- `type`: 记录类型
  - `sent`: 转出记录
  - `received`: 收到记录
  - `all`: 全部（默认）
- `page`: 页码（默认1）
- `limit`: 每页数量（默认20）

**响应示例**:
```json
{
  "success": true,
  "data": {
    "transfers": [
      {
        "transferId": "transfer_123456789",
        "type": "sent",             // 类型：sent|received
        "amount": 100,
        "recipientEmail": "friend@example.com",
        "senderEmail": "user@example.com",
        "message": "送给你的算力，祝使用愉快！",
        "status": "completed",      // 状态：pending|completed|failed
        "createdAt": "2023-12-01T10:35:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5,
      "totalPages": 1
    }
  },
  "message": "获取转赠记录成功"
}
```

## 算力消耗规则

### 基础算力消耗

| 功能 | 基础算力 | 备注 |
|------|----------|------|
| AI四方连续转换 | 60 | - |
| AI矢量化(转SVG) | 100 | 复杂度较高 |
| AI提取编辑 | 80 | 支持语音控制 |
| AI提取花型 | 100 | 需要预处理 |
| AI智能去水印 | 70 | - |
| AI布纹去噪 | 80 | 可选矢量重绘 |
| AI毛线刺绣增强 | 90 | 纹理处理复杂 |

### 附加算力规则

- **高分辨率**: 图片宽或高超过2048px时，算力消耗 ×1.5
- **大文件**: 文件大小超过10MB时，额外消耗20算力
- **复杂选项**: 某些高级选项可能增加额外算力消耗

### 会员折扣

- **高级会员**: 9折优惠
- **企业会员**: 8折优惠

## 错误码说明

| 错误码 | 说明 |
|-------|------|
| C001 | 算力不足 |
| C002 | 转赠数量超过余额 |
| C003 | 转赠对象不存在 |
| C004 | 不能向自己转赠算力 |
| C005 | 预警阈值设置无效 |
| C006 | 算力记录不存在 |
| C007 | 转赠功能已禁用 |
| C008 | 单次转赠数量超限 |
